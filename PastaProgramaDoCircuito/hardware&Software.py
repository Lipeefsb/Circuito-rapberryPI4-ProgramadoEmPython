import time
import random
import sys

# --- SOLUÇÃO PARA O ERRO DE IMPORT ---
try:
    import RPi.GPIO as GPIO
    MODO_SIMULACAO = False
except (ImportError, RuntimeError):
    # Se não estiver no Raspberry Pi, cria um Mock (simulador)
    from unittest.mock import MagicMock
    GPIO = MagicMock()
    MODO_SIMULACAO = True
    print("AVISO: Biblioteca RPi.GPIO não encontrada. Rodando em MODO DE SIMULAÇÃO.")

# --- Definição dos Pinos GPIO (Padrão BCM) ---
PIN_BOTAO = 17
PIN_ECHO = 24
PIN_TRIG = 23
PIN_LED_AMARELO = 27
PIN_LED_VERDE = 22
PIN_LED_VERMELHO = 5
PIN_BUZZER = 6

# --- Constantes do Jogo ---
LIMITE_EXCELENTE = 0.3 
LIMITE_MEDIO = 0.6 
VELOCIDADE_DO_SOM = 34300 
DISTANCIA_GATILHO = 10 

# --- Variáveis Globais ---
tempo_inicio_estmulo = 0.0
buzzer_pwm = None

# --- Funções de Controle ---

def limpar_saidas():
    """Desliga todos os LEDs e o Buzzer."""
    try:
        GPIO.output(PIN_LED_AMARELO, False)
        GPIO.output(PIN_LED_VERDE, False)
        GPIO.output(PIN_LED_VERMELHO, False)
        if buzzer_pwm and not MODO_SIMULACAO:
            buzzer_pwm.ChangeDutyCycle(0)
        else:
            GPIO.output(PIN_BUZZER, False)
    except Exception:
        pass

def configuracao_gpio():
    """Configura os pinos GPIO e inicializa o PWM para o buzzer."""
    global buzzer_pwm
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # Entradas e Saídas
    GPIO.setup(PIN_BOTAO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(PIN_ECHO, GPIO.IN)
    GPIO.setup(PIN_TRIG, GPIO.OUT)
    GPIO.setup(PIN_LED_AMARELO, GPIO.OUT)
    GPIO.setup(PIN_LED_VERDE, GPIO.OUT)
    GPIO.setup(PIN_LED_VERMELHO, GPIO.OUT)
    GPIO.setup(PIN_BUZZER, GPIO.OUT)

    GPIO.output(PIN_TRIG, False)
    
    if not MODO_SIMULACAO:
        buzzer_pwm = GPIO.PWM(PIN_BUZZER, 1000)
        buzzer_pwm.start(0)
    
    print("✅ GPIO configurado. Pronto para o teste.")

def tocar_tom(frequencia, duracao):
    """Gera som no buzzer. No modo simulação, apenas aguarda o tempo."""
    if not MODO_SIMULACAO and buzzer_pwm:
        if frequencia > 0:
            buzzer_pwm.ChangeFrequency(frequencia)
            buzzer_pwm.ChangeDutyCycle(50)
            time.sleep(duracao)
            buzzer_pwm.ChangeDutyCycle(0)
        else:
            time.sleep(duracao)
    else:
        time.sleep(duracao)

def medir_distancia():
    """Calcula a distância em cm usando o sensor HC-SR04."""
    if MODO_SIMULACAO:
        # Simula uma mão aproximando após 0.2s para teste de lógica
        return random.choice([50, 40, 5]) 

    GPIO.output(PIN_TRIG, True)
    time.sleep(0.00001)
    GPIO.output(PIN_TRIG, False)

    timeout = time.time()
    pulse_start = time.time()
    while GPIO.input(PIN_ECHO) == 0:
        pulse_start = time.time()
        if pulse_start - timeout > 0.1: return 999

    timeout = time.time()
    pulse_end = time.time()
    while GPIO.input(PIN_ECHO) == 1:
        pulse_end = time.time()
        if pulse_end - timeout > 0.1: return 999

    duracao_pulso = pulse_end - pulse_start
    return round((duracao_pulso * VELOCIDADE_DO_SOM) / 2, 2)

def mostrar_resultado(tempo_reacao):
    limpar_saidas()
    print(f"\n⏱️ TEMPO DE REAÇÃO: {tempo_reacao:.3f}s")

    if tempo_reacao <= LIMITE_EXCELENTE:
        print("🏆 REFLEXO: EXCELENTE!")
        GPIO.output(PIN_LED_VERDE, True)
        tocar_tom(1500, 0.2)
    elif tempo_reacao <= LIMITE_MEDIO:
        print("🟡 REFLEXO: MÉDIO.")
        for _ in range(3):
            GPIO.output(PIN_LED_AMARELO, True)
            time.sleep(0.1); GPIO.output(PIN_LED_AMARELO, False); time.sleep(0.1)
    else:
        print("🔴 REFLEXO: LENTO!")
        GPIO.output(PIN_LED_VERMELHO, True)
        tocar_tom(440, 1.0)
    
    time.sleep(2)
    limpar_saidas()
    print("\nPressione o botão para tentar novamente.")

def iniciar_teste(canal):
    global tempo_inicio_estmulo
    GPIO.remove_event_detect(PIN_BOTAO)
    
    print("\n--- TESTE INICIADO ---")
    GPIO.output(PIN_LED_AMARELO, True)
    time.sleep(random.uniform(2, 5))
    GPIO.output(PIN_LED_AMARELO, False)

    print("🔥 REAJA AGORA!")
    GPIO.output(PIN_LED_VERDE, True)
    tempo_inicio_estmulo = time.time()

    reagiu = False
    while (time.time() - tempo_inicio_estmulo) < 5.0:
        if medir_distancia() <= DISTANCIA_GATILHO:
            tempo_reacao = time.time() - tempo_inicio_estmulo
            mostrar_resultado(tempo_reacao)
            reagiu = True
            break
        time.sleep(0.01)

    if not reagiu:
        print("❌ TEMPO ESGOTADO!")
        mostrar_resultado(9.99)

    GPIO.add_event_detect(PIN_BOTAO, GPIO.RISING, callback=iniciar_teste, bouncetime=500)

# --- Main ---
if __name__ == "__main__":
    try:
        configuracao_gpio()
        GPIO.add_event_detect(PIN_BOTAO, GPIO.RISING, callback=iniciar_teste, bouncetime=500)
        print("Aguardando clique no botão (GPIO 17)...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nFinalizando...")
    finally:
        if not MODO_SIMULACAO:
            if buzzer_pwm: buzzer_pwm.stop()
            GPIO.cleanup()