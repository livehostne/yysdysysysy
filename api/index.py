# /api/index.py - Principal endpoint da Vercel
from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import time
import logging
from datetime import datetime

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TMDBProcessor:
    def __init__(self):
        self.status = {
            "last_run": None,
            "processed_count": 0,
            "failed_count": 0,
            "current_id": None,
            "status": "idle"
        }
        self.headers = {
            "Host": "spaceflix.online",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Windows\"",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
            "sec-ch-ua": "\"Microsoft Edge\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "Accept": "*/*",
            "Origin": "https://spaceflix.online",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://spaceflix.online/public/admin/tmdb-fetch?type=tv&q=prison&sortable=popularity.desc",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,pt-PT;q=0.5",
            "Cookie": "XSRF-TOKEN=eyJpdiI6Ildjdlh6TFA1MHAzSitjazMxUkdnYmc9PSIsInZhbHVlIjoidDZ3YWp5NURqM3A3ZmFyYzZEbk1BNFI3NkFxQzZibkFSWUZNYUhsdHNJZCs0c3FyK0lKM2Q0WUJINW1XZjdhQ1ZBUHpIMThKTE5BMlNsSyt1cGVhR3pYcFlrSnI2Y0JGa3dnZTQrczFUanNXQWlLc0c1bTY4TFcwSjhtaE1jRmYiLCJtYWMiOiI0NmZiNThhMmM0ZThiNDUyYzU3ZmNiYjY4OGJiMDFiNzBkZTNiOWJlNDYzOGQwOTMxYzI1NzE2MGViMmI3ZGRlIiwidGFnIjoiIn0%3D; laravel_session=eyJpdiI6InBiUVlRaHRPVWs5TmZKb1JaVm1aOVE9PSIsInZhbHVlIjoiZ3hwQ0ovc3RNaFc3eEtOSVJvUGY2SnE5YStPdjRyaUlGYnQ1ZDBSWlJUa25sNUR5UG44dVJOUjRlOUg5TVptSlp6OXNyS1hKTTB6bUM4a3lIV2htdW9MZUg0V1AyVWFnVXRUTE5oL09OUnZCUXpHcHpRek81UERCNllwSEhJN2QiLCJtYWMiOiJhMzVkMWJkYmQ0MGZkMTkxNDMyMTBjNDYzMmZlNjkxNzlhMzI5MTNiZGE2NWMwZTUxZDg5YmZhNzQ1MjM4YzVhIiwidGFnIjoiIn0%3D"
        }
        self.data = {
            "_token": "swlFQJWHasVf23nhNMiYdqbS08fPaq9RHvIBgTD4",
            "type": "movie",
            "import_people": "disable",
            "2embed": "disable",
            "vidsrc": "enable",
            "add_season": "disable",
            "add_episode": "disable"
        }
        
        # Inicializa arquivos JSON se não existirem
        self._init_json_files()
    
    def _init_json_files(self):
        """Verifica e cria arquivos JSON necessários se não existirem"""
        # Arquivo para armazenar status
        if not os.path.exists('status.json'):
            with open('status.json', 'w') as f:
                json.dump(self.status, f)
                
        # Arquivo para armazenar IDs processados
        if not os.path.exists('processed_ids.json'):
            with open('processed_ids.json', 'w') as f:
                json.dump([], f)
    
    def _get_ids_from_file(self):
        """Lê IDs do arquivo de texto"""
        try:
            # Caminho para o arquivo de IDs
            file_path = 'tmdb_ids.txt'
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    # Remove espaços em branco e linhas vazias
                    return [line.strip() for line in file if line.strip()]
            else:
                logger.error(f"Arquivo {file_path} não encontrado.")
                return []
        except Exception as e:
            logger.error(f"Erro ao ler IDs do arquivo: {str(e)}")
            return []
    
    def _get_processed_ids(self):
        """Obtém IDs já processados do arquivo JSON"""
        try:
            if os.path.exists('processed_ids.json'):
                with open('processed_ids.json', 'r') as file:
                    return set(json.load(file))
            return set()
        except Exception as e:
            logger.error(f"Erro ao ler IDs processados: {str(e)}")
            return set()
    
    def _save_processed_ids(self, processed_ids):
        """Salva IDs processados no arquivo JSON"""
        try:
            with open('processed_ids.json', 'w') as file:
                json.dump(list(processed_ids), file)
        except Exception as e:
            logger.error(f"Erro ao salvar IDs processados: {str(e)}")
    
    def _update_status(self):
        """Atualiza o arquivo de status"""
        try:
            with open('status.json', 'w') as file:
                json.dump(self.status, file)
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {str(e)}")
    
    def _load_status(self):
        """Carrega o status do arquivo"""
        try:
            if os.path.exists('status.json'):
                with open('status.json', 'r') as file:
                    saved_status = json.load(file)
                    # Atualiza apenas os campos necessários
                    for key in ['processed_count', 'failed_count']:
                        if key in saved_status:
                            self.status[key] = saved_status[key]
        except Exception as e:
            logger.error(f"Erro ao carregar status: {str(e)}")
    
    def _send_request(self, tmdb_id):
        """Envia uma requisição POST para um ID específico"""
        url = "https://spaceflix.online/public/admin/tmdb-store"
        
        # Atualiza o status
        self.status["current_id"] = tmdb_id
        self.status["status"] = "processing"
        self.status["last_run"] = datetime.now().isoformat()
        
        # Cria uma cópia dos dados para não modificar o original
        request_data = self.data.copy()
        request_data["tmdb_id"] = tmdb_id
        
        try:
            response = requests.post(url, headers=self.headers, data=request_data, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"ID {tmdb_id}: Requisição realizada com sucesso!")
                self.status["processed_count"] += 1
                self._update_status()
                return True
            else:
                logger.warning(f"ID {tmdb_id}: Falha - Status code: {response.status_code}")
                self.status["failed_count"] += 1
                self._update_status()
                return False
        except Exception as e:
            logger.error(f"ID {tmdb_id}: Erro: {str(e)}")
            self.status["failed_count"] += 1
            self._update_status()
            return False
    
    def process_batch(self, batch_size=1):
        """Processa um lote de IDs"""
        # Carrega o status atual
        self._load_status()
        
        tmdb_ids = self._get_ids_from_file()
        processed_ids = self._get_processed_ids()
        
        # Filtrar IDs que ainda não foram processados
        ids_to_process = [id for id in tmdb_ids if id not in processed_ids]
        
        if not ids_to_process:
            self.status["status"] = "completed"
            self._update_status()
            return {"status": "completed", "message": "Todos os IDs já foram processados"}
        
        # Pegar apenas o número de IDs definido por batch_size
        batch = ids_to_process[:batch_size]
        
        results = []
        for tmdb_id in batch:
            success = self._send_request(tmdb_id)
            results.append({"id": tmdb_id, "success": success})
            
            if success:
                # Adiciona o ID aos processados
                processed_ids.add(tmdb_id)
                self._save_processed_ids(processed_ids)
            
            # Pequena pausa para evitar sobrecarga
            time.sleep(1)
        
        self.status["status"] = "idle"
        self._update_status()
        
        return {
            "processed": results,
            "remaining": len(ids_to_process) - len(batch),
            "total_ids": len(tmdb_ids),
            "processed_total": len(processed_ids),
            "status": self.status
        }
    
    def get_status(self):
        """Retorna o status atual do processador"""
        # Carrega o status atual
        self._load_status()
        
        tmdb_ids = self._get_ids_from_file()
        processed_ids = self._get_processed_ids()
        ids_to_process = [id for id in tmdb_ids if id not in processed_ids]
        
        return {
            "status": self.status,
            "total_ids": len(tmdb_ids),
            "processed_total": len(processed_ids),
            "remaining": len(ids_to_process),
            "completion_percentage": round((len(processed_ids) / max(len(tmdb_ids), 1)) * 100, 2)
        }

# Instância global do processador
processor = TMDBProcessor()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Manipula requisições GET"""
        if self.path == '/api/status':
            # Retorna o status atual
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(processor.get_status()).encode())
        elif self.path == '/api/process':
            # Processa um lote de IDs
            result = processor.process_batch(batch_size=1)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            # Página inicial com instruções
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>TMDB Requester</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }
                    h1 { color: #333; text-align: center; }
                    h2 { margin-top: 20px; color: #444; }
                    .card { background: #f9f9f9; border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                    .button { background: #4CAF50; border: none; color: white; padding: 10px 20px; text-align: center; 
                             text-decoration: none; display: inline-block; font-size: 16px; margin: 10px 2px; cursor: pointer; border-radius: 4px; }
                    .button:hover { background: #45a049; }
                    .button:disabled { background: #cccccc; cursor: not-allowed; }
                    #status { white-space: pre-wrap; font-family: monospace; background: #f0f0f0; padding: 10px; max-height: 300px; overflow-y: auto; }
                    .auto-refresh { margin-top: 20px; }
                    .progress-container { width: 100%; background-color: #f1f1f1; border-radius: 5px; margin: 10px 0; }
                    .progress-bar { height: 30px; background-color: #4CAF50; border-radius: 5px; text-align: center; line-height: 30px; color: white; }
                    .status-box { display: flex; justify-content: space-between; margin-bottom: 20px; }
                    .status-item { text-align: center; flex: 1; padding: 10px; background: #f1f1f1; margin: 0 5px; border-radius: 5px; }
                    .status-item h3 { margin: 0; font-size: 14px; color: #666; }
                    .status-item p { margin: 5px 0 0; font-size: 18px; font-weight: bold; color: #333; }
                    .footer { margin-top: 40px; text-align: center; font-size: 12px; color: #777; }
                </style>
            </head>
            <body>
                <h1>TMDB Requester</h1>
                
                <div class="card">
                    <h2>Progresso do Processamento</h2>
                    <div class="status-box">
                        <div class="status-item">
                            <h3>Total de IDs</h3>
                            <p id="totalIds">-</p>
                        </div>
                        <div class="status-item">
                            <h3>Processados</h3>
                            <p id="processedIds">-</p>
                        </div>
                        <div class="status-item">
                            <h3>Restantes</h3>
                            <p id="remainingIds">-</p>
                        </div>
                        <div class="status-item">
                            <h3>Último ID</h3>
                            <p id="currentId">-</p>
                        </div>
                    </div>
                    
                    <div class="progress-container">
                        <div class="progress-bar" id="progressBar" style="width:0%">0%</div>
                    </div>
                    
                    <div class="auto-refresh">
                        <label><input type="checkbox" id="autoRefreshStatus"> Atualizar status automaticamente (5s)</label>
                    </div>
                </div>
                
                <div class="card">
                    <h2>Controles</h2>
                    <button class="button" id="processBtn" onclick="processOne()">Processar Um ID</button>
                    <div class="auto-refresh">
                        <label><input type="checkbox" id="autoProcess"> Auto-processar (10 segundos)</label>
                    </div>
                </div>
                
                <div class="card">
                    <h2>Detalhes do Status</h2>
                    <div id="status">Carregando...</div>
                    <button class="button" onclick="checkStatus()">Atualizar Status</button>
                </div>
                
                <div class="footer">
                    <p>TMDB Requester v1.0 - Processamento 24/7 na Vercel</p>
                </div>
                
                <script>
                    let autoRefreshInterval;
                    let autoProcessInterval;
                    
                    async function checkStatus() {
                        try {
                            const response = await fetch('/api/status');
                            const data = await response.json();
                            
                            // Atualizar detalhes do status
                            document.getElementById('status').innerText = JSON.stringify(data, null, 2);
                            
                            // Atualizar indicadores
                            document.getElementById('totalIds').innerText = data.total_ids;
                            document.getElementById('processedIds').innerText = data.processed_total;
                            document.getElementById('remainingIds').innerText = data.remaining;
                            document.getElementById('currentId').innerText = data.status.current_id || "-";
                            
                            // Atualizar barra de progresso
                            const progressBar = document.getElementById('progressBar');
                            const percentage = data.completion_percentage || 0;
                            progressBar.style.width = percentage + "%";
                            progressBar.innerText = percentage + "%";
                            
                            return data;
                        } catch (error) {
                            console.error('Erro ao verificar status:', error);
                            return null;
                        }
                    }
                    
                    async function processOne() {
                        const btn = document.getElementById('processBtn');
                        btn.disabled = true;
                        btn.innerText = 'Processando...';
                        
                        try {
                            const response = await fetch('/api/process');
                            const data = await response.json();
                            
                            // Atualizar status após processamento
                            await checkStatus();
                        } catch (error) {
                            console.error('Erro ao processar:', error);
                        }
                        
                        btn.disabled = false;
                        btn.innerText = 'Processar Um ID';
                    }
                    
                    // Controle de auto-refresh do status
                    document.getElementById('autoRefreshStatus').addEventListener('change', function(e) {
                        if (e.target.checked) {
                            autoRefreshInterval = setInterval(checkStatus, 5000);
                        } else {
                            clearInterval(autoRefreshInterval);
                        }
                    });
                    
                    // Controle de auto-processamento
                    document.getElementById('autoProcess').addEventListener('change', function(e) {
                        if (e.target.checked) {
                            autoProcessInterval = setInterval(processOne, 10000);
                        } else {
                            clearInterval(autoProcessInterval);
                        }
                    });
                    
                    // Carregar status inicial
                    checkStatus();
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())

def handler(request, context):
    """Função handler para Vercel Serverless Functions"""
    return Handler().handle_request(request)
