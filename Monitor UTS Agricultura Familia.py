import serial
import time
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext
import queue
import tkinter as tk
from tkinter import ttk

class DashboardAgricola:
    def __init__(self, root):
        self.root = root
        self.root.title("🌱 PAINEL DE CONTROLE - PROTÓTIPO AGRÍCOLA")
        self.root.geometry("800x600")
        self.root.configure(bg='#1a1a2e')
        
        # Configurações
        self.porta_usb = 'COM11'
        self.velocidade = 9600
        self.arduino = None
        self.dados_queue = queue.Queue()
        self.conectado = False
        
        # Dados para gráficos simples
        self.historico_dados = []
        self.max_historico = 50
        
        self.setup_ui()
        self.conectar_arduino()
        
        # Iniciar thread de leitura
        self.running = True
        self.thread_leitura = threading.Thread(target=self.ler_dados_arduino, daemon=True)
        self.thread_leitura.start()
        
        # Atualizar interface periodicamente
        self.atualizar_interface()
    
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Estilo
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Data.TLabel', font=('Courier', 12))
        style.configure('Status.TLabel', font=('Arial', 10))
        
        # Título
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="🌾 SISTEMA DE MONITORAMENTO AGRÍCOLA", 
                 style='Title.TLabel').pack()
        
        # Status da conexão
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(self.status_frame, text="Status: Desconectado", 
                                      style='Status.TLabel', foreground='red')
        self.status_label.pack(side=tk.LEFT)
        
        self.led_status = tk.Canvas(self.status_frame, width=20, height=20, bg='#1a1a2e', 
                                    highlightthickness=0)
        self.led_status.pack(side=tk.LEFT, padx=10)
        self.led_conexao = self.led_status.create_oval(2, 2, 18, 18, fill='red')
        
        # Dashboard com cards
        cards_frame = ttk.Frame(main_frame)
        cards_frame.pack(fill=tk.X, pady=10)
        
        # Card: Último valor recebido
        self.card_valor = self.criar_card(cards_frame, "Último Valor Recebido", "Aguardando...")
        self.card_valor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Card: Total de leituras
        self.card_leituras = self.criar_card(cards_frame, "Leituras de Estabilização (50)", "0")
        self.card_leituras.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Card: Status do sensor
        self.card_status = self.criar_card(cards_frame, "Status do Sensor", "Inativo")
        self.card_status.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Gráfico ASCII
        grafico_frame = ttk.LabelFrame(main_frame, text="Histórico de Leituras", padding="10")
        grafico_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.grafico_text = scrolledtext.ScrolledText(grafico_frame, height=10, 
                                                      font=('Courier', 10))
        self.grafico_text.pack(fill=tk.BOTH, expand=True)
        
        # Console de dados
        console_frame = ttk.LabelFrame(main_frame, text="Log de Dados", padding="10")
        console_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.console_text = scrolledtext.ScrolledText(console_frame, height=8, 
                                                      font=('Courier', 9))
        self.console_text.pack(fill=tk.BOTH, expand=True)
        
        # Botões de controle

        style = ttk.Style()
        style.configure(
            "Blue.TButton",
            background="#0078D7",
            foreground="blue",
            font=('Arial', 10, 'bold'),
            padding=7
        )
        style.map(
            "Blue.TButton",
            background=[("active","#005A9E"),("pressed", "#004578")]

            )
        style.configure(
            "Green.TButton",
            background="#2E7D32",
            foreground="green",
            font=('Arial', 10, 'bold'),
            padding=7
            
        )
        style.map(
            "Green.TButton",
            background=[("active","#1B5E20"),("pressed", "#145A18")]

            )
        style.configure(
            "Yellow.TButton",
            background="#F9A825",
            foreground="#111111",
            font=('Arial', 10, 'bold'),
            padding=7
        )
        style.map(
            "Yellow.TButton",
            background=[("active","#F57F17"),("pressed", "#E65100")],
            foreground=[("active","#111111"),("pressed", "#111111")]

            )
        style.configure(
            "Red.TButton",
            background="#C62828",
            foreground="red",
            font=('Arial', 10, 'bold'),
            padding=7
        )
        style.map(
            "Red.TButton",
            background=[("active","#B71C1C"),("pressed", "#8@0000")]

            )
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="🔄 ⏎ Reconectar", 
                  command=self.reconectar, style="Blue.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✉♥ Exportar Log", 
                  command=self.exportar_log, style="Green.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑 ✐ ️ Limpar Console", 
                  command=self.limpar_console, style="Yellow.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ ⌦ Sair", 
                  command=self.fechar, style="Red.TButton").pack(side=tk.RIGHT, padx=5)
        
        # Barra de progresso
        self.progressbar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progressbar.pack(fill=tk.X, pady=5)
    
    def criar_card(self, parent, titulo, valor_inicial):
        frame = tk.Frame(parent, bg='#16213e', relief=tk.RAISED, bd=2)
        
        tk.Label(frame, text=titulo, bg='#16213e', fg='#e94560', 
                font=('Arial', 10, 'bold')).pack(pady=5)
        
        label_valor = tk.Label(frame, text=valor_inicial, bg='#16213e', fg='white', 
                               font=('Arial', 14, 'bold'))
        label_valor.pack(pady=10)
        
        return frame
    
    def conectar_arduino(self):
        try:
            if self.arduino and self.arduino.is_open:
                self.arduino.close()
            
            self.arduino = serial.Serial(self.porta_usb, self.velocidade, timeout=1)
            time.sleep(2)
            
            self.conectado = True
            self.atualizar_status("Conectado", 'green')
            self.log_console("✅ Conexão estabelecida com Arduino!")
            
        except Exception as e:
            self.conectado = False
            self.atualizar_status(f"Erro: {str(e)[:30]}", 'red')
            self.log_console(f"❌ ERRO: {str(e)}")
    
    def atualizar_status(self, mensagem, cor):
        self.status_label.config(text=f"Status: {mensagem}", foreground=cor)
        self.led_status.itemconfig(self.led_conexao, fill=cor)
        
        if self.conectado:
            self.progressbar.start()
        else:
            self.progressbar.stop()
    
    def ler_dados_arduino(self):
        while self.running:
            if self.conectado and self.arduino and self.arduino.is_open:
                try:
                    if self.arduino.in_waiting > 0:
                        linha = self.arduino.readline().decode('utf-8').strip()
                        if linha:
                            self.dados_queue.put(linha)
                except Exception as e:
                    self.dados_queue.put(f"ERRO: {str(e)}")
                    self.conectado = False
            time.sleep(0.1)
    
    def atualizar_interface(self):
        try:
            while True:
                dados = self.dados_queue.get_nowait()
                self.processar_dados(dados)
        except queue.Empty:
            pass
        
        if self.running:
            self.root.after(100, self.atualizar_interface)
    
    def processar_dados(self, dados):
        agora = datetime.now().strftime("%H:%M:%S")
        
        # Console log
        self.log_console(f"[{agora}] {dados}")
        
        # Atualizar cards
        if not dados.startswith("ERRO"):
            # Atualizar último valor
            self.atualizar_card_valor(self.card_valor, dados)
            
            # Atualizar contador
            self.historico_dados.append(dados)
            if len(self.historico_dados) > self.max_historico:
                self.historico_dados.pop(0)
            
            self.atualizar_card_valor(self.card_leituras, str(len(self.historico_dados)))
            
            # Atualizar status do sensor
            self.atualizar_card_valor(self.card_status, "Ativo")
            
            # Atualizar gráfico ASCII
            self.atualizar_grafico()
    
    def atualizar_card_valor(self, card, valor):
        for widget in card.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget('font') == 'Arial 14 bold':
                widget.config(text=valor[:20])
    
    def atualizar_grafico(self):
        self.grafico_text.delete(1.0, tk.END)
        
        if not self.historico_dados:
            self.grafico_text.insert(tk.END, "Aguardando dados...")
            return
        
        # Criar gráfico ASCII simples
        try:
            valores = []
            for dado in self.historico_dados[-self.max_historico:]:
                try:
                    # Tenta extrair número do dado
                    num = float(''.join(filter(lambda x: x.isdigit() or x == '.', dado)))
                    valores.append(num)
                except:
                    valores.append(0)
            
            if valores:
                max_val = max(valores) if max(valores) > 0 else 1
                min_val = min(valores)
                
                altura_grafico = 10
                
                for i in range(altura_grafico, 0, -1):
                    linha = ""
                    for val in valores:
                        altura_ponto = int((val - min_val) / (max_val - min_val) * altura_grafico) if max_val > min_val else 0
                        if altura_ponto >= i:
                            linha += "█"
                        else:
                            linha += " "
                    self.grafico_text.insert(tk.END, linha + "\n")
                
                self.grafico_text.insert(tk.END, "─" * len(valores) + "\n")
                self.grafico_text.insert(tk.END, f"Min: {min_val:.1f}  Max: {max_val:.1f}  Último: {valores[-1]:.1f}")
                
        except Exception as e:
            self.grafico_text.insert(tk.END, f"Erro ao gerar gráfico: {str(e)}")
    
    def log_console(self, mensagem):
        self.console_text.insert(tk.END, mensagem + "\n")
        self.console_text.see(tk.END)
        # Limitar número de linhas
        if int(self.console_text.index('end-1c').split('.')[0]) > 100:
            self.console_text.delete(1.0, 2.0)
    
    def reconectar(self):
        self.log_console("🔄 Tentando reconectar...")
        self.conectar_arduino()
    
    def exportar_log(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"log_agricola_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write(self.console_text.get(1.0, tk.END))
            
            self.log_console(f"✅ Log exportado para {filename}")
            
        except Exception as e:
            self.log_console(f"❌ Erro ao exportar: {str(e)}")
    
    def limpar_console(self):
        self.console_text.delete(1.0, tk.END)
        self.historico_dados.clear()
        self.grafico_text.delete(1.0, tk.END)
        self.log_console("🗑️ Console limpo!")
    
    def fechar(self):
        self.running = False
        if self.arduino and self.arduino.is_open:
            self.arduino.close()
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardAgricola(root)
    root.protocol("WM_DELETE_WINDOW", app.fechar)
    root.mainloop()
