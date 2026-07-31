# =============================================================================
# 🤖 SISTEMA HÍBRIDO ULTRA ROBUSTO CON INTERFAZ VISUAL COMPLETA — v6 /GOD (∞)
# =============================================================================
# MÚLTIPLES FUENTES GRATUITAS - PRECIOS REALES EN TIEMPO REAL
# TODAS LAS METODOLOGÍAS ORIGINALES + FALLOVER AUTOMÁTICO
# + TRANSFORMER PROFUNDO (NumPy puro: 4 capas, 4 cabezas, d_model=64,
#   d_ff=256, dropout, GELU, LayerNorm, Adam) ENTRENADO CON DATOS REALES
#   Y REENTRENADO AUTOMÁTICAMENTE CADA 200 CICLOS EN SEGUNDO PLANO.
# =============================================================================

import cv2
import numpy as np
import mss
import os
import re
import time
from datetime import datetime, timedelta
from collections import deque, Counter
import sys
import warnings
import concurrent.futures
import threading
import requests
import json

# =============================================================================
# IMPORTACIONES Y VERIFICACIONES
# =============================================================================

print("\n" + "="*120)
print("🤖 SISTEMA HÍBRIDO ULTRA ROBUSTO - DIVISAS FOREX (MÚLTIPLES FUENTES)")
print("   PRECIOS REALES EN TIEMPO REAL - FALLOVER AUTOMÁTICO")
print("   🧠 TRANSFORMER PROFUNDO INTEGRADO (NumPy, 4L/4H/d64) — v6 /GOD")
print("="*120)

try:
    import pyautogui
    TRADING_DISPONIBLE = True
    print("✅ PyAutoGUI disponible")
except ImportError:
    TRADING_DISPONIBLE = False
    print("⚠️ PyAutoGUI no instalado (trading manual)")

try:
    import pandas as pd
    print("✅ Pandas disponible")
except ImportError:
    pd = None
    print("⚠️ Pandas no instalado")

try:
    from scipy import stats
    from scipy.stats import skew, kurtosis
    SCIPY_DISPONIBLE = True
    print("✅ SciPy disponible")
except ImportError:
    SCIPY_DISPONIBLE = False
    print("⚠️ SciPy no instalado")

try:
    import yfinance as yf
    YF_AVAILABLE = True
    print("✅ yfinance disponible")
except ImportError:
    YF_AVAILABLE = False
    print("⚠️ yfinance no instalado (se usarán otras fuentes)")

try:
    import pytesseract
    for _ruta_tess in (r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'):
        if os.path.exists(_ruta_tess):
            pytesseract.pytesseract.tesseract_cmd = _ruta_tess
            break
    PYTESSERACT_DISPONIBLE = True
    print("✅ pytesseract disponible (lectura OCR de Capital activada)")
except ImportError:
    PYTESSERACT_DISPONIBLE = False
    print("⚠️ pytesseract no instalado — el Capital Tracker quedará inactivo "
          "(pip install pytesseract, y el binario Tesseract-OCR en el sistema)")

try:
    import keyboard
    KEYBOARD_DISPONIBLE = True
    print("✅ keyboard disponible (calibración de coordenadas con ENTER global)")
except ImportError:
    KEYBOARD_DISPONIBLE = False
    print("⚠️ keyboard no instalado — la calibración de coordenadas usará ENTER en "
          "esta consola en vez de captura global (pip install keyboard para mejor experiencia)")

warnings.filterwarnings('ignore')

# =============================================================================
# 🏦 YAHOO FINANCE CORE (CACHÉ, PRECIOS, VELAS)
# =============================================================================

class YahooFinanceCore:
    """Clase central para obtener datos de Yahoo Finance con caché y manejo robusto."""

    def __init__(self):
        self.cache = {}
        self.cache_time = {}
        self.cache_seconds = 1

    # -----------------------------------------------------
    # Obtener ticker Yahoo (formato correcto)
    # -----------------------------------------------------
    def _ticker(self, symbol):
        symbol = symbol.upper().replace("/", "")
        if not symbol.endswith("=X"):
            symbol = f"{symbol}=X"
        return yf.Ticker(symbol)

    # -----------------------------------------------------
    # Precio actual (último close de vela de 1m)
    # -----------------------------------------------------
    def get_price(self, symbol):
        try:
            ticker = self._ticker(symbol)
            hist = ticker.history(period="1d", interval="1m")
            if hist.empty:
                return None
            return float(hist["Close"].iloc[-1])
        except Exception as e:
            print(f"[YF] Error get_price: {e}")
            return None

    # -----------------------------------------------------
    # Última vela completa (OHLCV + tiempo)
    # -----------------------------------------------------
    def get_last_candle(self, symbol):
        try:
            ticker = self._ticker(symbol)
            hist = ticker.history(period="1d", interval="1m")
            if hist.empty:
                return None
            row = hist.iloc[-1]
            return {
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": float(row["Volume"]),
                "time": str(hist.index[-1])
            }
        except Exception as e:
            print(f"[YF] Error candle: {e}")
            return None

    # -----------------------------------------------------
    # OHLC histórico (DataFrame)
    # -----------------------------------------------------
    def get_ohlc(self, symbol, period="1d", interval="1m"):
        try:
            ticker = self._ticker(symbol)
            return ticker.history(period=period, interval=interval)
        except Exception as e:
            print(f"[YF] Error OHLC: {e}")
            return pd.DataFrame()

    # -----------------------------------------------------
    # Obtener N cierres recientes
    # -----------------------------------------------------
    def get_closes(self, symbol, candles=100):
        data = self.get_ohlc(symbol, period="5d", interval="1m")
        if data.empty:
            return []
        return data["Close"].tail(candles).tolist()

    # -----------------------------------------------------
    # Precio con caché (evita múltiples llamadas)
    # -----------------------------------------------------
    def get_price_cached(self, symbol):
        now = time.time()
        if (symbol in self.cache and
            now - self.cache_time.get(symbol, 0) < self.cache_seconds):
            return self.cache[symbol]

        price = self.get_price(symbol)
        if price:
            self.cache[symbol] = price
            self.cache_time[symbol] = now
        return price

    # -----------------------------------------------------
    # Snapshot completo de mercado
    # -----------------------------------------------------
    def get_market_snapshot(self, symbol):
        candle = self.get_last_candle(symbol)
        if candle is None:
            return None
        return {
            "symbol": symbol,
            "price": candle["close"],
            "open": candle["open"],
            "high": candle["high"],
            "low": candle["low"],
            "volume": candle["volume"],
            "timestamp": datetime.now()
        }

# =============================================================================
# CONFIGURACIÓN GLOBAL (ORIGINAL)
# =============================================================================

class ConfigGlobal:
    MONITOR = {"top": 147, "left": 79, "width": 1639, "height": 887}
    VELAS_A_ANALIZAR = 20
    MIN_MECHA_RATIO = 0.5
    TIEMPO_VELA_SEGUNDOS = 60
    TIMEFRAME_SEGUNDOS = None
    TIMEFRAME_LABEL = None
    YF_INTERVAL = "1m"
    YF_PERIODS_PRECIO = ["1d", "5d", "1mo"]
    YF_PERIODS_HISTORICO = ["5d", "7d", "1mo"]

    DIVISAS = [
        {"symbol": "EURUSD=X", "name": "Euro/Dólar",       "color": "#003399", "volatility": 0.005, "weight": 0.20},
        {"symbol": "GBPUSD=X", "name": "Libra/Dólar",      "color": "#003399", "volatility": 0.006, "weight": 0.15},
        {"symbol": "USDJPY=X", "name": "Dólar/Yen",        "color": "#BC002D", "volatility": 0.005, "weight": 0.15},
        {"symbol": "USDCHF=X", "name": "Dólar/Franco",     "color": "#FF0000", "volatility": 0.005, "weight": 0.10},
        {"symbol": "AUDUSD=X", "name": "Australiano/USD",  "color": "#00008B", "volatility": 0.007, "weight": 0.10},
        {"symbol": "USDCAD=X", "name": "Dólar/Canadiense", "color": "#FF0000", "volatility": 0.005, "weight": 0.10},
        {"symbol": "NZDUSD=X", "name": "Neozelandés/USD",  "color": "#00247D", "volatility": 0.007, "weight": 0.10},
        {"symbol": "EURGBP=X", "name": "Euro/Libra",       "color": "#003399", "volatility": 0.004, "weight": 0.10},
    ]
    CRYPTOS = DIVISAS
    DIVISA_ACTIVA = None

    UPDATE_INTERVAL = 30
    HISTORY_POINTS = 60
    PARALLEL_WORKERS = 4
    API_TIMEOUT = 7
    UMBRAL_SEÑALES_COMPRA = 3
    UMBRAL_SEÑALES_VENTA = 3
    COOLDOWN_CICLOS = 2

    METHODOLOGIES = [
        "Price Action Analysis", "Break of Structure (BOS)", "Pin Bar Detection",
        "False Breakout Detection", "Support & Resistance", "Institutional Analysis",
        "Quantum Processing", "Linear Regression", "Yield Anomaly Detection",
        "Statistical Arbitrage", "Multi-Timeframe Confirmation", "Smart Money Concepts",
        "MACD (8,21,5)", "Stochastic (14,3)", "RSI (14)", "Bollinger Bands (20,2)", "ATR (14)"
    ]

    # --- Parámetros de indicadores técnicos (incorporados de SAOTT156) ---
    MACD_FAST = 8
    MACD_SLOW = 21
    MACD_SIGNAL = 5
    STOCH_K = 14
    STOCH_D = 3
    STOCH_OVERBOUGHT = 75
    STOCH_OVERSOLD = 25
    RSI_PERIOD = 14
    BB_PERIOD = 20
    BB_STD = 2
    ATR_PERIOD = 14

    # --- 🧠 Parámetros del Transformer profundo (NumPy puro) ---
    TRANSFORMER_SEQ_LEN = 30          # longitud de la ventana de entrada (timesteps)
    TRANSFORMER_D_MODEL = 64          # dimensión del modelo
    TRANSFORMER_N_HEADS = 4           # cabezas de atención
    TRANSFORMER_N_LAYERS = 4          # capas del encoder
    TRANSFORMER_D_FF = 256            # dimensión feed-forward interna
    TRANSFORMER_DROPOUT = 0.1         # dropout
    TRANSFORMER_LR = 1e-3             # learning rate Adam
    TRANSFORMER_EPOCHS_INIT = 60      # épocas en el entrenamiento inicial
    TRANSFORMER_EPOCHS_RETRAIN = 25   # épocas en cada reentrenamiento
    TRANSFORMER_BATCH_SIZE = 32
    TRANSFORMER_MIN_CLOSES = 500      # cierres reales mínimos deseados al iniciar
    TRANSFORMER_MIN_CLOSES_FLOOR = 80 # mínimo absoluto para poder entrenar algo
    TRANSFORMER_RETRAIN_CICLOS = 500  # reentrenar cada N ciclos del sistema
    TRANSFORMER_WEIGHT = 2.2          # peso de su señal dentro del híbrido
    TRANSFORMER_CONF_MIN = 0.55       # confianza mínima del Transformer para sumar señal

    # --- 💾 Persistencia de pesos del Transformer entre sesiones ---
    TRANSFORMER_MODEL_DIR = "transformer_models"   # carpeta donde se guardan los .npz por símbolo
    TRANSFORMER_MODEL_MAX_AGE_HOURS = 48           # si el checkpoint es más reciente que esto, sólo se hace ajuste fino
    TRANSFORMER_EPOCHS_FINE_TUNE = 8               # épocas de ajuste fino al cargar un modelo ya entrenado

    # --- 💰 Capital Tracker (OCR) — región de pantalla donde se muestra el saldo ---
    # Ajusta estos valores a la posición real del número de capital en tu bróker.
    MONITOR_CAPITAL = {"top": 83, "left": 1551, "width": 107, "height": 41}
    CAPITAL_OCR_ENABLED = True             # si no hay pytesseract, se desactiva solo
    CAPITAL_CHECK_INTERVAL_SEGUNDOS = 62   # cada cuánto se lee el capital (igual que Capital_registro v1.3)

    # --- 🧠 Refuerzo tipo Q-Learning: aprender de operaciones ganadas/perdidas ---
    CAPITAL_REINFORCE_ENABLED = True
    CAPITAL_REINFORCE_MIN_BATCH = 4        # mínimo de patrones (replay) por paso de refuerzo
    CAPITAL_REINFORCE_MAX_REPLAY = 8       # tamaño máx. del mini-batch de repetición de experiencia
    CAPITAL_PATTERN_MEMORY_MAX = 2000      # patrones ganados/perdidos guardados en memoria persistente

    # --- 🖱️ Coordenadas de click (compra/venta) y calibración persistente ---
    # Valores por defecto (se sobrescriben si el usuario calibra al iniciar).
    BUY_COORDS = (1820, 449)
    SELL_COORDS = (1819, 509)
    COORDS_CONFIG_FILE = "coordenadas_config.json"

# =============================================================================
# 💰 CAPITAL TRACKER — OCR del saldo real + registro de ganadas/perdidas
#     (integra la lógica de "Capital_registro_vs1_3.py" dentro del sistema
#     híbrido, usando el mismo backend de captura `mss` que ya usa el resto
#     del programa, en vez de pyautogui, para no duplicar dependencias).
# =============================================================================

class CapitalTracker:
    """
    Lee por OCR el número de capital/saldo mostrado en pantalla
    (ConfigGlobal.MONITOR_CAPITAL), calcula la diferencia respecto a la
    lectura anterior y al capital inicial, y clasifica cada lectura como
    GANADA / PERDIDA / NEUTRA / INICIAL. Ese registro se usa luego para:
      1) el informe final (capital inicial, final y diferencia global), y
      2) reforzar al Transformer con el resultado REAL de cada operación
         (ver AdvancedDecisionSystem / TransformerSignalEngine).
    """

    def __init__(self, monitor=None):
        self.sct = mss.mss()
        self.monitor = monitor or ConfigGlobal.MONITOR_CAPITAL
        self.capital_inicial = None
        self.capital_actual = None
        self._ultimo_capital = None
        self.registro = []
        self.lock = threading.Lock()
        self.habilitado = bool(ConfigGlobal.CAPITAL_OCR_ENABLED and PYTESSERACT_DISPONIBLE)
        if not self.habilitado:
            print("⚠️ [Capital] OCR de capital deshabilitado "
                  f"(pytesseract={'sí' if PYTESSERACT_DISPONIBLE else 'no'}, "
                  f"config={ConfigGlobal.CAPITAL_OCR_ENABLED}). El sistema seguirá "
                  "funcionando con normalidad, pero sin refuerzo por capital real.")

    # -----------------------------------------------------------
    # Captura de la región del capital usando `mss` (consistente
    # con capturar_pantalla() del resto del sistema)
    # -----------------------------------------------------------
    def _capturar_region(self):
        try:
            raw = np.array(self.sct.grab(self.monitor))
            return cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)
        except Exception as e:
            print(f"⚠️ [Capital] Error capturando región de pantalla: {e}")
            return None

    # -----------------------------------------------------------
    # Preprocesado multi-variante para robustecer el OCR (idéntico
    # criterio al de Capital_registro_vs1_3: varias transformaciones,
    # se vota por el resultado más frecuente/largo)
    # -----------------------------------------------------------
    @staticmethod
    def _procesar_para_ocr(imagen):
        gray = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        variantes = []
        variantes.append(cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC))
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        variantes.append(cv2.resize(clahe.apply(gray), None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC))
        thresh_adapt = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                              cv2.THRESH_BINARY, 11, 2)
        variantes.append(cv2.resize(thresh_adapt, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC))
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph_close = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        variantes.append(cv2.resize(morph_close, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC))
        kernel_sharpen = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharp = cv2.filter2D(gray, -1, kernel_sharpen)
        variantes.append(cv2.resize(sharp, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC))
        variantes.append(cv2.resize(cv2.bitwise_not(gray), None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC))
        return variantes

    @staticmethod
    def _extraer_numero(texto):
        if not texto:
            return None
        limpio = re.sub(r'[^\d,.\-]', ' ', texto)
        patrones = [
            r'\-?\d{1,3}(?:,\d{3})*(?:\.\d+)?',
            r'\-?\d{1,3}(?:\.\d{3})*(?:,\d+)?',
            r'\-?\d+(?:\.\d+)?',
            r'\-?\d+(?:,\d+)?'
        ]
        candidatos = []
        for patron in patrones:
            candidatos.extend(re.findall(patron, limpio))
        if not candidatos:
            return None
        mejor = max(candidatos, key=len)
        try:
            if ',' in mejor and '.' in mejor:
                numero_str = mejor.replace(',', '') if mejor.rfind(',') < mejor.rfind('.') \
                    else mejor.replace('.', '').replace(',', '.')
            elif ',' in mejor:
                numero_str = mejor.replace(',', '.') if (mejor.count(',') == 1 and len(mejor) > 4
                                                           and mejor[-3] == ',') else mejor.replace(',', '')
            elif '.' in mejor:
                numero_str = mejor.replace('.', '') if mejor.count('.') > 1 else mejor
            else:
                numero_str = mejor
            return float(numero_str)
        except Exception:
            return None

    def _leer_numero_ocr(self, imagen):
        candidatos = []
        for img in self._procesar_para_ocr(imagen):
            for psm in (6, 7, 8, 13):
                try:
                    config = f'--oem 3 --psm {psm} -c tessedit_char_whitelist=0123456789.,-'
                    texto = pytesseract.image_to_string(img, config=config)
                    numero = self._extraer_numero(texto)
                    if numero is not None:
                        candidatos.append((numero, len(str(int(abs(numero))))))
                except Exception:
                    continue
        if not candidatos:
            return None
        redondeados = [round(n, 2) for n, _ in candidatos]
        mas_frecuente = Counter(redondeados).most_common(1)[0][0]
        mejores = [(n, l) for n, l in candidatos if round(n, 2) == mas_frecuente]
        return max(mejores, key=lambda x: x[1])[0]

    def leer_capital(self):
        """Lectura puntual del capital actual (o None si no se pudo leer)."""
        if not self.habilitado:
            return None
        imagen = self._capturar_region()
        if imagen is None:
            return None
        return self._leer_numero_ocr(imagen)

    def actualizar(self):
        """Lee el capital, actualiza el registro con diferencias vs. anterior
        y vs. inicial, y devuelve la entrada registrada (o None)."""
        numero = self.leer_capital()
        if numero is None:
            return None
        with self.lock:
            timestamp = datetime.now()
            if self.capital_inicial is None:
                self.capital_inicial = numero
                self.capital_actual = numero
                self._ultimo_capital = numero
                entrada = {"timestamp": timestamp, "capital": numero,
                           "diff_prev": 0.0, "var_prev": 0.0,
                           "diff_init": 0.0, "var_init": 0.0, "resultado": "INICIAL"}
                self.registro.append(entrada)
                print(f"\n💰 [Capital] CAPITAL INICIAL detectado: C$ {numero:,.2f}")
                return entrada

            diff_prev = numero - self._ultimo_capital
            var_prev = (diff_prev / self._ultimo_capital * 100) if self._ultimo_capital else 0.0
            diff_init = numero - self.capital_inicial
            var_init = (diff_init / self.capital_inicial * 100) if self.capital_inicial else 0.0
            if diff_prev > 1e-9:
                resultado = "GANADA"
            elif diff_prev < -1e-9:
                resultado = "PERDIDA"
            else:
                resultado = "NEUTRA"
            entrada = {"timestamp": timestamp, "capital": numero,
                       "diff_prev": diff_prev, "var_prev": var_prev,
                       "diff_init": diff_init, "var_init": var_init, "resultado": resultado}
            self.registro.append(entrada)
            self.capital_actual = numero
            self._ultimo_capital = numero
            signo = '+' if diff_prev >= 0 else ''
            print(f"\n💰 [Capital] {resultado}: C$ {numero:,.2f}  "
                  f"(vs ant: {signo}{diff_prev:,.2f}, {var_prev:+.2f}%)")
            return entrada

    def resumen_final(self):
        if self.capital_inicial is None or self.capital_actual is None:
            return None
        diferencia = self.capital_actual - self.capital_inicial
        variacion = (diferencia / self.capital_inicial * 100) if self.capital_inicial else 0.0
        return {
            "capital_inicial": self.capital_inicial,
            "capital_final": self.capital_actual,
            "diferencia": diferencia,
            "variacion_pct": variacion,
            "n_lecturas": len(self.registro)
        }


# =============================================================================
# 🧭 CALIBRADOR DE COORDENADAS — configuración guiada previa al arranque
#     (unifica y mejora "Cordenadapantalla.py" y "ver_coordenadas.py")
# =============================================================================

class CoordinateCalibrator:
    """
    Asistente de calibración de coordenadas de pantalla, ejecutado ANTES de
    iniciar el sistema. Unifica y mejora dos utilidades que antes eran
    scripts sueltos:

      - "Cordenadapantalla.py" -> aquí se usa para calibrar DOS regiones:
          1) MONITOR: el recuadro del gráfico de velas (Price Action / OCR
             visual), tal cual el script original (4 esquinas).
          2) MONITOR_CAPITAL: el recuadro donde se muestra el saldo/capital,
             con el mismo criterio pero simplificado a 2 esquinas, ya que es
             un rectángulo pequeño de texto.

      - "ver_coordenadas.py" -> mejorado: en vez de un bucle infinito que
        sólo se podía cortar con Ctrl+C (lo que mataba todo el proceso),
        ahora muestra la posición del mouse EN VIVO y se fija el punto con
        ENTER, reutilizando esa lectura para calibrar, uno a uno, el punto
        de click de COMPRA y el de VENTA.

    Todo el resultado se guarda en un JSON (ConfigGlobal.COORDS_CONFIG_FILE)
    para no tener que repetir la calibración en cada sesión: al arrancar,
    el sistema pregunta si se quiere reutilizar la configuración guardada,
    recalibrar, o seguir con los valores por defecto de ConfigGlobal.
    """

    def __init__(self):
        self.filepath = ConfigGlobal.COORDS_CONFIG_FILE

    # -----------------------------------------------------------
    # Espera de ENTER: global (con `keyboard`) o en la consola (fallback)
    # -----------------------------------------------------------
    @staticmethod
    def _esperar_enter():
        if KEYBOARD_DISPONIBLE:
            keyboard.wait("enter")
        else:
            input()

    def _capturar_punto(self, nombre, instrucciones=""):
        print(f"\n➡️  Coloca el mouse en: {nombre}")
        if instrucciones:
            print(f"    {instrucciones}")
        if KEYBOARD_DISPONIBLE:
            print("⏳ Presiona ENTER (puedes tenerlo enfocado en el gráfico/bróker)...")
        else:
            print("⏳ Presiona ENTER en ESTA CONSOLA (instala 'keyboard' para no perder el foco)...")
        self._esperar_enter()
        x, y = pyautogui.position()
        print(f"✅ {nombre}: X={x}, Y={y}")
        time.sleep(0.4)
        return x, y

    # -----------------------------------------------------------
    # 🖼️ Vista previa: captura la región recién calibrada y la muestra en
    #     una ventana (ampliada si es pequeña, como el capital) para que el
    #     usuario confirme el encuadre ANTES de guardar. Si no hay entorno
    #     gráfico disponible, se guarda igualmente un PNG en disco.
    # -----------------------------------------------------------
    def _mostrar_preview(self, monitor, nombre_region):
        try:
            with mss.mss() as sct:
                raw = np.array(sct.grab(monitor))
            img_bgr = cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)
        except Exception as e:
            print(f"⚠️ No se pudo capturar la vista previa de '{nombre_region}': {e}")
            return None

        h, w = img_bgr.shape[:2]
        # Amplía regiones pequeñas (p.ej. el capital, de ~100x40px) para que
        # se vean con claridad; las regiones grandes (el gráfico) se dejan igual.
        escala = max(1, min(6, 400 // max(1, w)))
        img_preview = (cv2.resize(img_bgr, (w * escala, h * escala), interpolation=cv2.INTER_NEAREST)
                        if escala > 1 else img_bgr)

        archivo = f"preview_{nombre_region.lower().replace(' ', '_')}.png"
        try:
            cv2.imwrite(archivo, img_preview)
        except Exception:
            archivo = None

        titulo = f"Vista previa: {nombre_region}  (cualquier tecla para cerrar)"
        mostrado_en_ventana = False
        try:
            cv2.namedWindow(titulo, cv2.WINDOW_NORMAL)
            cv2.imshow(titulo, img_preview)
            print(f"\n🖼️  Vista previa de '{nombre_region}' abierta en una ventana "
                  f"({w}x{h}px capturados). Presiona cualquier tecla sobre la ventana para continuar.")
            cv2.waitKey(0)
            cv2.destroyWindow(titulo)
            mostrado_en_ventana = True
        except Exception as e:
            print(f"⚠️ No se pudo abrir una ventana de vista previa ({e}).")

        if archivo:
            extra = "" if mostrado_en_ventana else " — ábrela manualmente para revisar el encuadre"
            print(f"💾 Vista previa guardada en: {archivo}{extra}")
        return archivo

    def _confirmar_encuadre(self, monitor, nombre_region):
        """Muestra la vista previa y pregunta si el encuadre quedó correcto.
        Devuelve True si el usuario confirma, False si pide recalibrar."""
        self._mostrar_preview(monitor, nombre_region)
        resp = input(f"\n¿'{nombre_region}' quedó bien encuadrado? "
                      "(s = sí, continuar / n = recalibrar esta región): ").strip().lower()
        return resp != 'n'

    # -----------------------------------------------------------
    # 🖼️ MONITOR del gráfico (Price Action) — 4 esquinas, mismo criterio
    #     que Cordenadapantalla.py, aplicado ahora dentro del sistema.
    #     Incluye vista previa con confirmación antes de aceptarlo.
    # -----------------------------------------------------------
    def calibrar_monitor_grafico(self):
        while True:
            print("\n" + "="*60)
            print("🎯 CALIBRACIÓN: REGIÓN DEL GRÁFICO (velas / Price Action)")
            print("="*60)
            sup_izq = self._capturar_punto("ESQUINA SUPERIOR IZQUIERDA del gráfico")
            sup_der = self._capturar_punto("ESQUINA SUPERIOR DERECHA del gráfico")
            inf_izq = self._capturar_punto("ESQUINA INFERIOR IZQUIERDA del gráfico")
            left, top = sup_izq
            right = sup_der[0]
            bottom = inf_izq[1]
            monitor = {"top": top, "left": left, "width": max(1, right - left), "height": max(1, bottom - top)}
            print(f"\n📐 MONITOR (gráfico): {monitor}")
            if self._confirmar_encuadre(monitor, "Gráfico (Price Action)"):
                return monitor
            print("🔁 Repitiendo calibración de la región del gráfico...")

    # -----------------------------------------------------------
    # 💰 MONITOR_CAPITAL — región pequeña del saldo: 2 esquinas bastan
    #     (adaptación de Cordenadapantalla.py para un recuadro de texto)
    # -----------------------------------------------------------
    def calibrar_monitor_capital(self):
        while True:
            print("\n" + "="*60)
            print("💰 CALIBRACIÓN: REGIÓN DEL CAPITAL / SALDO")
            print("="*60)
            sup_izq = self._capturar_punto("ESQUINA SUPERIOR IZQUIERDA del número de capital",
                                            "Justo antes del primer dígito/símbolo")
            inf_der = self._capturar_punto("ESQUINA INFERIOR DERECHA del número de capital",
                                            "Justo después del último dígito")
            left, top = sup_izq
            right, bottom = inf_der
            monitor = {"top": top, "left": left, "width": max(1, right - left), "height": max(1, bottom - top)}
            print(f"\n📐 MONITOR_CAPITAL: {monitor}")
            if self._confirmar_encuadre(monitor, "Capital / Saldo"):
                return monitor
            print("🔁 Repitiendo calibración de la región del capital...")

    # -----------------------------------------------------------
    # 🖱️ Puntos de click COMPRA / VENTA — versión mejorada de
    #     ver_coordenadas.py: posición en vivo + fijación con ENTER,
    #     en vez de un bucle sólo interrumpible con Ctrl+C.
    # -----------------------------------------------------------
    @staticmethod
    def _vivo_hasta_enter():
        while True:
            if keyboard.is_pressed("enter"):
                time.sleep(0.15)  # evita rebote / doble lectura del mismo ENTER
                return
            x, y = pyautogui.position()
            print(f"   📍 X={x:5d}  Y={y:5d}   (ENTER para fijar el punto)", end="\r")
            time.sleep(0.03)

    def calibrar_click(self, nombre):
        print("\n" + "="*60)
        print(f"🖱️  CALIBRACIÓN DE CLICK: {nombre}")
        print("="*60)
        print("Mueve el mouse sobre el botón correspondiente en tu bróker.")
        if KEYBOARD_DISPONIBLE:
            print("Verás la posición del mouse en vivo. Presiona ENTER para fijarla.")
            self._vivo_hasta_enter()
            x, y = pyautogui.position()
            print()  # salto de línea tras el print con end="\r"
        else:
            print("(Instala 'pip install keyboard' para ver la posición en vivo sin perder "
                  "el foco de la ventana del bróker.)")
            print("Posiciona el mouse y presiona ENTER en ESTA CONSOLA cuando estés listo...")
            input()
            x, y = pyautogui.position()
        print(f"✅ {nombre}: X={x}, Y={y}")
        return (x, y)

    # -----------------------------------------------------------
    # 💾 Persistencia entre sesiones
    # -----------------------------------------------------------
    def guardar(self, datos):
        try:
            datos = dict(datos)
            datos["calibrado_en"] = datetime.now().isoformat()
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Coordenadas guardadas en: {self.filepath}")
        except Exception as e:
            print(f"⚠️ No se pudieron guardar las coordenadas: {e}")

    def cargar(self):
        if not os.path.exists(self.filepath):
            return None
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ No se pudo leer la configuración guardada ({e}); se recalibrará.")
            return None

    # -----------------------------------------------------------
    # 🚀 Flujo completo guiado: gráfico -> capital -> compra -> venta
    # -----------------------------------------------------------
    def ejecutar_calibracion_completa(self):
        print("\n" + "#"*70)
        print("# 🧭 ASISTENTE DE CALIBRACIÓN DE COORDENADAS DEL SISTEMA")
        print("#"*70)
        monitor = self.calibrar_monitor_grafico()
        monitor_capital = self.calibrar_monitor_capital()
        buy_coords = self.calibrar_click("BOTÓN DE COMPRA")
        sell_coords = self.calibrar_click("BOTÓN DE VENTA")
        datos = {
            "MONITOR": monitor,
            "MONITOR_CAPITAL": monitor_capital,
            "BUY_COORDS": list(buy_coords),
            "SELL_COORDS": list(sell_coords),
        }
        self.guardar(datos)
        return datos

    def aplicar(self, datos):
        """Aplica un dict de coordenadas (recién calibrado o cargado de disco)
        a ConfigGlobal, sin romper la estructura ni funcionalidades del resto
        del sistema — todo lo que ya usaba ConfigGlobal.MONITOR / MONITOR_CAPITAL
        / BUY_COORDS / SELL_COORDS sigue funcionando igual."""
        if not datos:
            return
        if "MONITOR" in datos:
            ConfigGlobal.MONITOR = dict(datos["MONITOR"])
        if "MONITOR_CAPITAL" in datos:
            ConfigGlobal.MONITOR_CAPITAL = dict(datos["MONITOR_CAPITAL"])
        if "BUY_COORDS" in datos:
            ConfigGlobal.BUY_COORDS = tuple(datos["BUY_COORDS"])
        if "SELL_COORDS" in datos:
            ConfigGlobal.SELL_COORDS = tuple(datos["SELL_COORDS"])
        print("\n✅ Coordenadas aplicadas a la configuración del sistema:")
        print(f"   MONITOR         = {ConfigGlobal.MONITOR}")
        print(f"   MONITOR_CAPITAL = {ConfigGlobal.MONITOR_CAPITAL}")
        print(f"   BUY_COORDS      = {ConfigGlobal.BUY_COORDS}")
        print(f"   SELL_COORDS     = {ConfigGlobal.SELL_COORDS}")


def configurar_coordenadas_si_necesario():
    """
    Se ejecuta ANTES de crear el AdvancedTradingSystem. Ofrece:
      1) Reutilizar una calibración guardada de una sesión anterior, o
      2) Calibrar ahora (gráfico + capital + clicks de compra/venta), o
      3) Continuar con los valores por defecto ya definidos en ConfigGlobal.
    Si PyAutoGUI no está disponible, se omite automáticamente (no tiene
    sentido calibrar clicks/regiones sin poder leer la posición del mouse).
    """
    if not TRADING_DISPONIBLE:
        print("⚠️ PyAutoGUI no disponible: se omite la calibración de coordenadas "
              "y se usan los valores por defecto ya definidos en ConfigGlobal.")
        return
    calibrador = CoordinateCalibrator()
    guardado = calibrador.cargar()
    print("\n" + "="*70)
    print("⚙️  CONFIGURACIÓN DE COORDENADAS DE PANTALLA")
    print("="*70)
    if guardado:
        print(f"💾 Se encontró una configuración guardada ({guardado.get('calibrado_en', '?')}):")
        print(f"   MONITOR         = {guardado.get('MONITOR')}")
        print(f"   MONITOR_CAPITAL = {guardado.get('MONITOR_CAPITAL')}")
        print(f"   BUY_COORDS      = {guardado.get('BUY_COORDS')}")
        print(f"   SELL_COORDS     = {guardado.get('SELL_COORDS')}")
        resp = input("\n¿Usar esta configuración guardada? (s = usar / n = recalibrar): ").strip().lower()
        if resp == 's':
            calibrador.aplicar(guardado)
            return
    resp2 = input("\n¿Deseas calibrar ahora el gráfico, el capital y los clicks de "
                  "compra/venta? (s/n): ").strip().lower()
    if resp2 == 's':
        datos = calibrador.ejecutar_calibracion_completa()
        calibrador.aplicar(datos)
    else:
        print("ℹ️ Se usarán las coordenadas por defecto de ConfigGlobal "
              f"(puedes recalibrar luego borrando {calibrador.filepath}).")


# =============================================================================
# 📐 UTILIDADES MATEMÁTICAS (incorporado de SAOTT156, código verificado sin
#     generación de datos falsos: sólo funciones matemáticas puras)
# =============================================================================

class MathUtils:
    @staticmethod
    def ema(data, period):
        if not data:
            return []
        alpha = 2.0 / (period + 1)
        ema_vals = [data[0]]
        for price in data[1:]:
            ema_vals.append(alpha * price + (1 - alpha) * ema_vals[-1])
        return ema_vals

    @staticmethod
    def safe_mean(arr, default=0.0):
        try:
            return float(np.mean(arr)) if arr else default
        except Exception:
            return default

    @staticmethod
    def safe_std(arr, default=0.01):
        try:
            return float(np.std(arr)) if arr and len(arr) >= 2 else default
        except Exception:
            return default

# =============================================================================
# 📊 ANALIZADOR DE INDICADORES TÉCNICOS (MACD, Estocástico, RSI, Bollinger, ATR)
# Calculado siempre sobre precios/velas REALES (closes de Yahoo Finance vía
# UnifiedForexDataProvider) — sin valores simulados ni aleatorios.
# =============================================================================

class TechnicalIndicatorAnalyzer:
    def __init__(self):
        self.macd_fast = ConfigGlobal.MACD_FAST
        self.macd_slow = ConfigGlobal.MACD_SLOW
        self.macd_signal = ConfigGlobal.MACD_SIGNAL
        self.stoch_k = ConfigGlobal.STOCH_K
        self.stoch_d = ConfigGlobal.STOCH_D
        self.overbought = ConfigGlobal.STOCH_OVERBOUGHT
        self.oversold = ConfigGlobal.STOCH_OVERSOLD
        self.rsi_period = ConfigGlobal.RSI_PERIOD
        self.bb_period = ConfigGlobal.BB_PERIOD
        self.bb_std = ConfigGlobal.BB_STD
        self.atr_period = ConfigGlobal.ATR_PERIOD

    def compute_macd(self, prices):
        if len(prices) < self.macd_slow + 1:
            return {'macd': 0, 'signal': 0, 'histogram': 0, 'trend': 'NEUTRAL', 'cruce': False}
        try:
            ema_fast = MathUtils.ema(prices, self.macd_fast)
            ema_slow = MathUtils.ema(prices, self.macd_slow)
            min_len = min(len(ema_fast), len(ema_slow))
            macd_line = [ema_fast[i] - ema_slow[i] for i in range(min_len)]
            signal_line = MathUtils.ema(macd_line, self.macd_signal)
            hist_len = min(len(macd_line), len(signal_line))
            histogram = [macd_line[i] - signal_line[i] for i in range(hist_len)]
            if len(histogram) >= 2:
                if histogram[-1] > 0 and histogram[-2] <= 0:
                    trend = 'ALCISTA_CRUCE'
                elif histogram[-1] < 0 and histogram[-2] >= 0:
                    trend = 'BAJISTA_CRUCE'
                elif histogram[-1] > 0:
                    trend = 'ALCISTA'
                elif histogram[-1] < 0:
                    trend = 'BAJISTA'
                else:
                    trend = 'NEUTRAL'
            else:
                trend = 'NEUTRAL'
            return {
                'macd': float(macd_line[-1]) if macd_line else 0,
                'signal': float(signal_line[-1]) if signal_line else 0,
                'histogram': float(histogram[-1]) if histogram else 0,
                'trend': trend,
                'cruce': trend.endswith('CRUCE')
            }
        except Exception:
            return {'macd': 0, 'signal': 0, 'histogram': 0, 'trend': 'NEUTRAL', 'cruce': False}

    def compute_stochastic(self, prices):
        if len(prices) < self.stoch_k:
            return {'k': 50, 'd': 50, 'position': 'NEUTRAL', 'cruce': False}
        try:
            n = len(prices)
            fast_k = []
            for i in range(n):
                window = prices[max(0, i - self.stoch_k + 1):i + 1]
                highest, lowest = max(window), min(window)
                fast_k.append(50 if highest - lowest == 0 else 100 * (prices[i] - lowest) / (highest - lowest))
            slow_k = []
            for i in range(n):
                window_k = fast_k[max(0, i - self.stoch_d + 1):i + 1]
                slow_k.append(sum(window_k) / len(window_k))
            slow_d = []
            for i in range(n):
                window_k = slow_k[max(0, i - self.stoch_d + 1):i + 1]
                slow_d.append(sum(window_k) / len(window_k))
            k_val, d_val = slow_k[-1], slow_d[-1]
            cruce = False
            if len(slow_k) >= 2 and len(slow_d) >= 2:
                if slow_k[-2] <= slow_d[-2] and slow_k[-1] > slow_d[-1]:
                    cruce = 'ALCISTA'
                elif slow_k[-2] >= slow_d[-2] and slow_k[-1] < slow_d[-1]:
                    cruce = 'BAJISTA'
            if k_val > self.overbought and d_val > self.overbought:
                position = 'SOBRECOMPRA'
            elif k_val < self.oversold and d_val < self.oversold:
                position = 'SOBREVENTA'
            else:
                position = 'NEUTRAL'
            return {'k': float(k_val), 'd': float(d_val), 'position': position, 'cruce': cruce}
        except Exception:
            return {'k': 50, 'd': 50, 'position': 'NEUTRAL', 'cruce': False}

    def compute_rsi(self, prices, period=None):
        period = period or self.rsi_period
        if len(prices) < period + 1:
            return {'rsi': 50, 'position': 'NEUTRAL'}
        try:
            deltas = [prices[i + 1] - prices[i] for i in range(len(prices) - 1)]
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            rsi = 100 if avg_loss == 0 else 100 - (100 / (1 + (avg_gain / avg_loss)))
            position = 'SOBRECOMPRA' if rsi > 70 else ('SOBREVENTA' if rsi < 30 else 'NEUTRAL')
            return {'rsi': float(rsi), 'position': position}
        except Exception:
            return {'rsi': 50, 'position': 'NEUTRAL'}

    def compute_bollinger(self, prices, period=None, num_std=None):
        period = period or self.bb_period
        num_std = num_std or self.bb_std
        if len(prices) < period:
            return {'upper': None, 'middle': None, 'lower': None, 'position': 'NEUTRAL'}
        try:
            window = prices[-period:]
            mid = sum(window) / period
            std = (sum((p - mid) ** 2 for p in window) / period) ** 0.5
            upper = mid + num_std * std
            lower = mid - num_std * std
            last = prices[-1]
            if last >= upper:
                position = 'SOBRE_BANDA_SUPERIOR'
            elif last <= lower:
                position = 'SOBRE_BANDA_INFERIOR'
            else:
                position = 'DENTRO_DE_BANDAS'
            return {'upper': float(upper), 'middle': float(mid), 'lower': float(lower), 'position': position}
        except Exception:
            return {'upper': None, 'middle': None, 'lower': None, 'position': 'NEUTRAL'}

    def compute_atr(self, highs, lows, closes, period=None):
        """Average True Range a partir de máximos/mínimos/cierres reales."""
        period = period or self.atr_period
        if len(highs) < period + 1 or len(lows) < period + 1 or len(closes) < period + 1:
            return {'atr': 0.0}
        try:
            trs = []
            for i in range(1, len(closes)):
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i - 1]),
                    abs(lows[i] - closes[i - 1])
                )
                trs.append(tr)
            atr = sum(trs[-period:]) / period
            return {'atr': float(atr)}
        except Exception:
            return {'atr': 0.0}

# =============================================================================
# 🧠 TRANSFORMER PROFUNDO (NumPy PURO) — 4 capas / 4 cabezas / d_model=64
# =============================================================================
# Implementación completa desde cero (forward + backward manual + Adam):
#   - Embedding lineal de features + Positional Encoding senoidal
#   - N capas de encoder: Multi-Head Self-Attention + Feed-Forward (GELU)
#   - LayerNorm (pre-norm) + conexiones residuales + Dropout
#   - Cabezal de clasificación binaria (sube/baja) con softmax
#   - Optimizador Adam implementado manualmente (sin frameworks externos)
# Entrena con cierres REALES (Yahoo Finance) de la divisa activa.
# =============================================================================

def _gelu(x):
    """GELU (aproximación tanh, estable numéricamente)."""
    return 0.5 * x * (1.0 + np.tanh(np.sqrt(2.0 / np.pi) * (x + 0.044715 * np.power(x, 3))))

def _gelu_grad(x):
    """Derivada de la aproximación tanh de GELU."""
    c = np.sqrt(2.0 / np.pi)
    x3 = np.power(x, 3)
    tanh_arg = c * (x + 0.044715 * x3)
    t = np.tanh(tanh_arg)
    sech2 = 1.0 - t * t
    d_tanh_arg = c * (1.0 + 3 * 0.044715 * np.power(x, 2))
    return 0.5 * (1.0 + t) + 0.5 * x * sech2 * d_tanh_arg

def _softmax(x, axis=-1):
    x = x - np.max(x, axis=axis, keepdims=True)
    e = np.exp(x)
    return e / (np.sum(e, axis=axis, keepdims=True) + 1e-12)


class AdamOptimizer:
    """Optimizador Adam implementado manualmente, parámetro a parámetro."""
    def __init__(self, lr=1e-3, beta1=0.9, beta2=0.999, eps=1e-8):
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.m = {}
        self.v = {}
        self.t = 0

    def step(self, params, grads):
        self.t += 1
        for key in params:
            if key not in grads or grads[key] is None:
                continue
            g = grads[key]
            if key not in self.m:
                self.m[key] = np.zeros_like(params[key])
                self.v[key] = np.zeros_like(params[key])
            self.m[key] = self.beta1 * self.m[key] + (1 - self.beta1) * g
            self.v[key] = self.beta2 * self.v[key] + (1 - self.beta2) * (g * g)
            m_hat = self.m[key] / (1 - self.beta1 ** self.t)
            v_hat = self.v[key] / (1 - self.beta2 ** self.t)
            params[key] -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)


class LayerNorm:
    """Layer Normalization con parámetros entrenables gamma/beta."""
    def __init__(self, d_model, name):
        self.name = name
        self.gamma = np.ones((d_model,), dtype=np.float64)
        self.beta = np.zeros((d_model,), dtype=np.float64)
        self.eps = 1e-6
        self._cache = None

    def params(self):
        return {f"{self.name}_gamma": self.gamma, f"{self.name}_beta": self.beta}

    def load_params(self, p):
        self.gamma = p[f"{self.name}_gamma"]
        self.beta = p[f"{self.name}_beta"]

    def forward(self, x):
        mu = np.mean(x, axis=-1, keepdims=True)
        var = np.var(x, axis=-1, keepdims=True)
        x_norm = (x - mu) / np.sqrt(var + self.eps)
        out = self.gamma * x_norm + self.beta
        self._cache = (x, x_norm, mu, var)
        return out

    def backward(self, dout):
        x, x_norm, mu, var = self._cache
        N = x.shape[-1]
        d_gamma = np.sum(dout * x_norm, axis=tuple(range(dout.ndim - 1)))
        d_beta = np.sum(dout, axis=tuple(range(dout.ndim - 1)))
        dx_norm = dout * self.gamma
        std_inv = 1.0 / np.sqrt(var + self.eps)
        dvar = np.sum(dx_norm * (x - mu) * -0.5 * std_inv ** 3, axis=-1, keepdims=True)
        dmu = np.sum(dx_norm * -std_inv, axis=-1, keepdims=True) + dvar * np.mean(-2.0 * (x - mu), axis=-1, keepdims=True)
        dx = dx_norm * std_inv + dvar * 2.0 * (x - mu) / N + dmu / N
        grads = {f"{self.name}_gamma": d_gamma, f"{self.name}_beta": d_beta}
        return dx, grads


class Dropout:
    """Dropout estándar (sólo activo en modo entrenamiento)."""
    def __init__(self, rate):
        self.rate = rate
        self.mask = None

    def forward(self, x, training):
        if not training or self.rate <= 0:
            self.mask = None
            return x
        self.mask = (np.random.rand(*x.shape) > self.rate) / (1.0 - self.rate)
        return x * self.mask

    def backward(self, dout):
        if self.mask is None:
            return dout
        return dout * self.mask


class MultiHeadSelfAttention:
    """Auto-atención multi-cabeza con proyecciones Q,K,V,O entrenables."""
    def __init__(self, d_model, n_heads, name):
        self.name = name
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads
        scale = np.sqrt(2.0 / (d_model + d_model))
        rng = np.random.default_rng(abs(hash(name)) % (2**31))
        self.Wq = (rng.standard_normal((d_model, d_model)) * scale)
        self.Wk = (rng.standard_normal((d_model, d_model)) * scale)
        self.Wv = (rng.standard_normal((d_model, d_model)) * scale)
        self.Wo = (rng.standard_normal((d_model, d_model)) * scale)
        self.bq = np.zeros((d_model,))
        self.bk = np.zeros((d_model,))
        self.bv = np.zeros((d_model,))
        self.bo = np.zeros((d_model,))
        self._cache = None

    def params(self):
        return {
            f"{self.name}_Wq": self.Wq, f"{self.name}_Wk": self.Wk,
            f"{self.name}_Wv": self.Wv, f"{self.name}_Wo": self.Wo,
            f"{self.name}_bq": self.bq, f"{self.name}_bk": self.bk,
            f"{self.name}_bv": self.bv, f"{self.name}_bo": self.bo,
        }

    def load_params(self, p):
        self.Wq, self.Wk, self.Wv, self.Wo = p[f"{self.name}_Wq"], p[f"{self.name}_Wk"], p[f"{self.name}_Wv"], p[f"{self.name}_Wo"]
        self.bq, self.bk, self.bv, self.bo = p[f"{self.name}_bq"], p[f"{self.name}_bk"], p[f"{self.name}_bv"], p[f"{self.name}_bo"]

    def _split_heads(self, x):
        B, T, D = x.shape
        x = x.reshape(B, T, self.n_heads, self.d_k)
        return x.transpose(0, 2, 1, 3)  # (B, H, T, d_k)

    def _merge_heads(self, x):
        B, H, T, d_k = x.shape
        x = x.transpose(0, 2, 1, 3)
        return x.reshape(B, T, H * d_k)

    def forward(self, x):
        B, T, D = x.shape
        Q = x @ self.Wq + self.bq
        K = x @ self.Wk + self.bk
        V = x @ self.Wv + self.bv
        Qh, Kh, Vh = self._split_heads(Q), self._split_heads(K), self._split_heads(V)
        scores = Qh @ Kh.transpose(0, 1, 3, 2) / np.sqrt(self.d_k)  # (B,H,T,T)
        attn = _softmax(scores, axis=-1)
        context = attn @ Vh  # (B,H,T,d_k)
        merged = self._merge_heads(context)  # (B,T,D)
        out = merged @ self.Wo + self.bo
        self._cache = (x, Q, K, V, Qh, Kh, Vh, attn, merged)
        return out

    def backward(self, dout):
        x, Q, K, V, Qh, Kh, Vh, attn, merged = self._cache
        B, T, D = x.shape

        d_merged = dout @ self.Wo.T
        d_Wo = merged.reshape(-1, D).T @ dout.reshape(-1, D)
        d_bo = np.sum(dout, axis=(0, 1))

        d_context = self._split_heads(d_merged)  # (B,H,T,d_k)
        d_attn = d_context @ Vh.transpose(0, 1, 3, 2)  # (B,H,T,T)
        d_Vh = attn.transpose(0, 1, 3, 2) @ d_context  # (B,H,T,d_k)

        # softmax backward
        s = attn
        d_scores = s * (d_attn - np.sum(d_attn * s, axis=-1, keepdims=True))
        d_scores = d_scores / np.sqrt(self.d_k)

        d_Qh = d_scores @ Kh
        d_Kh = d_scores.transpose(0, 1, 3, 2) @ Qh

        d_Q = self._merge_heads(d_Qh)
        d_K = self._merge_heads(d_Kh)
        d_V = self._merge_heads(d_Vh)

        d_Wq = x.reshape(-1, D).T @ d_Q.reshape(-1, D)
        d_Wk = x.reshape(-1, D).T @ d_K.reshape(-1, D)
        d_Wv = x.reshape(-1, D).T @ d_V.reshape(-1, D)
        d_bq = np.sum(d_Q, axis=(0, 1))
        d_bk = np.sum(d_K, axis=(0, 1))
        d_bv = np.sum(d_V, axis=(0, 1))

        dx = d_Q @ self.Wq.T + d_K @ self.Wk.T + d_V @ self.Wv.T

        grads = {
            f"{self.name}_Wq": d_Wq, f"{self.name}_Wk": d_Wk,
            f"{self.name}_Wv": d_Wv, f"{self.name}_Wo": d_Wo,
            f"{self.name}_bq": d_bq, f"{self.name}_bk": d_bk,
            f"{self.name}_bv": d_bv, f"{self.name}_bo": d_bo,
        }
        return dx, grads


class FeedForward:
    """Bloque Feed-Forward posicional: Linear -> GELU -> Linear."""
    def __init__(self, d_model, d_ff, name):
        self.name = name
        rng = np.random.default_rng(abs(hash(name)) % (2**31))
        self.W1 = rng.standard_normal((d_model, d_ff)) * np.sqrt(2.0 / d_model)
        self.b1 = np.zeros((d_ff,))
        self.W2 = rng.standard_normal((d_ff, d_model)) * np.sqrt(2.0 / d_ff)
        self.b2 = np.zeros((d_model,))
        self._cache = None

    def params(self):
        return {f"{self.name}_W1": self.W1, f"{self.name}_b1": self.b1,
                f"{self.name}_W2": self.W2, f"{self.name}_b2": self.b2}

    def load_params(self, p):
        self.W1, self.b1 = p[f"{self.name}_W1"], p[f"{self.name}_b1"]
        self.W2, self.b2 = p[f"{self.name}_W2"], p[f"{self.name}_b2"]

    def forward(self, x):
        z1 = x @ self.W1 + self.b1
        a1 = _gelu(z1)
        z2 = a1 @ self.W2 + self.b2
        self._cache = (x, z1, a1)
        return z2

    def backward(self, dout):
        x, z1, a1 = self._cache
        D, F = self.W1.shape
        d_W2 = a1.reshape(-1, F).T @ dout.reshape(-1, dout.shape[-1])
        d_b2 = np.sum(dout, axis=(0, 1))
        d_a1 = dout @ self.W2.T
        d_z1 = d_a1 * _gelu_grad(z1)
        d_W1 = x.reshape(-1, D).T @ d_z1.reshape(-1, F)
        d_b1 = np.sum(d_z1, axis=(0, 1))
        dx = d_z1 @ self.W1.T
        grads = {f"{self.name}_W1": d_W1, f"{self.name}_b1": d_b1,
                 f"{self.name}_W2": d_W2, f"{self.name}_b2": d_b2}
        return dx, grads


class TransformerEncoderLayer:
    """Capa de encoder: Pre-LN Self-Attention + Pre-LN FeedForward, residuales + dropout."""
    def __init__(self, d_model, n_heads, d_ff, dropout, idx):
        self.attn = MultiHeadSelfAttention(d_model, n_heads, f"L{idx}_attn")
        self.ff = FeedForward(d_model, d_ff, f"L{idx}_ff")
        self.ln1 = LayerNorm(d_model, f"L{idx}_ln1")
        self.ln2 = LayerNorm(d_model, f"L{idx}_ln2")
        self.drop1 = Dropout(dropout)
        self.drop2 = Dropout(dropout)

    def params(self):
        p = {}
        p.update(self.attn.params()); p.update(self.ff.params())
        p.update(self.ln1.params()); p.update(self.ln2.params())
        return p

    def load_params(self, p):
        self.attn.load_params(p); self.ff.load_params(p)
        self.ln1.load_params(p); self.ln2.load_params(p)

    def forward(self, x, training):
        n1 = self.ln1.forward(x)
        a = self.attn.forward(n1)
        a = self.drop1.forward(a, training)
        x = x + a
        n2 = self.ln2.forward(x)
        f = self.ff.forward(n2)
        f = self.drop2.forward(f, training)
        x = x + f
        return x

    def backward(self, dout):
        grads = {}
        d_f = self.drop2.backward(dout)
        d_n2, g_ff = self.ff.backward(d_f)
        d_ln2_x, g_ln2 = self.ln2.backward(d_n2)
        d_after_attn = dout + d_ln2_x  # residual

        d_a = self.drop1.backward(d_after_attn)
        d_n1, g_attn = self.attn.backward(d_a)
        d_ln1_x, g_ln1 = self.ln1.backward(d_n1)
        dx = d_after_attn + d_ln1_x  # residual

        grads.update(g_ff); grads.update(g_ln2); grads.update(g_attn); grads.update(g_ln1)
        return dx, grads


class DeepTransformer:
    """
    Transformer profundo completo en NumPy puro:
      - 4 capas de encoder, 4 cabezas de atención, d_model=64, d_ff=256
      - Dropout, GELU, LayerNorm, conexiones residuales
      - Embedding lineal de entrada + Positional Encoding senoidal
      - Cabezal de clasificación binaria (sube / baja) vía softmax
      - Entrenamiento con Adam y backpropagation manual end-to-end
    """
    def __init__(self, n_features, seq_len=None, d_model=None, n_heads=None,
                 n_layers=None, d_ff=None, dropout=None, lr=None):
        self.n_features = n_features
        self.seq_len = seq_len or ConfigGlobal.TRANSFORMER_SEQ_LEN
        self.d_model = d_model or ConfigGlobal.TRANSFORMER_D_MODEL
        self.n_heads = n_heads or ConfigGlobal.TRANSFORMER_N_HEADS
        self.n_layers = n_layers or ConfigGlobal.TRANSFORMER_N_LAYERS
        self.d_ff = d_ff or ConfigGlobal.TRANSFORMER_D_FF
        self.dropout = dropout if dropout is not None else ConfigGlobal.TRANSFORMER_DROPOUT
        self.lr = lr or ConfigGlobal.TRANSFORMER_LR

        rng = np.random.default_rng(42)
        self.W_embed = rng.standard_normal((self.n_features, self.d_model)) * np.sqrt(2.0 / self.n_features)
        self.b_embed = np.zeros((self.d_model,))
        self.pos_encoding = self._build_positional_encoding(self.seq_len, self.d_model)

        self.layers = [
            TransformerEncoderLayer(self.d_model, self.n_heads, self.d_ff, self.dropout, i)
            for i in range(self.n_layers)
        ]
        self.ln_final = LayerNorm(self.d_model, "final_ln")

        self.W_out = rng.standard_normal((self.d_model, 2)) * np.sqrt(2.0 / self.d_model)
        self.b_out = np.zeros((2,))

        self.optimizer = AdamOptimizer(lr=self.lr)
        self.trained_steps = 0
        self.last_train_loss = None
        self.last_train_acc = None
        self.is_trained = False
        self._loaded_saved_at = None

    @staticmethod
    def _build_positional_encoding(seq_len, d_model):
        pe = np.zeros((seq_len, d_model))
        position = np.arange(0, seq_len).reshape(-1, 1)
        div_term = np.exp(np.arange(0, d_model, 2) * -(np.log(10000.0) / d_model))
        pe[:, 0::2] = np.sin(position * div_term)
        pe[:, 1::2] = np.cos(position * div_term[: pe[:, 1::2].shape[1]])
        return pe

    def get_all_params(self):
        p = {"W_embed": self.W_embed, "b_embed": self.b_embed,
             "W_out": self.W_out, "b_out": self.b_out}
        for layer in self.layers:
            p.update(layer.params())
        p.update(self.ln_final.params())
        return p

    def load_all_params(self, p):
        self.W_embed, self.b_embed = p["W_embed"], p["b_embed"]
        self.W_out, self.b_out = p["W_out"], p["b_out"]
        for layer in self.layers:
            layer.load_params(p)
        self.ln_final.load_params(p)

    # ---------------------------------------------------------------
    # 💾 Persistencia de pesos entre sesiones (np.savez / np.load)
    # ---------------------------------------------------------------
    def save_weights(self, filepath):
        """Guarda todos los pesos del modelo, el estado del optimizador Adam
        (m, v, t — permite reanudar el entrenamiento exactamente donde se quedó)
        y metadatos (arquitectura, progreso) en un único archivo .npz."""
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)

        save_dict = {}
        for k, v in self.get_all_params().items():
            save_dict[f"param__{k}"] = v
        for k, v in self.optimizer.m.items():
            save_dict[f"optm__{k}"] = v
        for k, v in self.optimizer.v.items():
            save_dict[f"optv__{k}"] = v
        save_dict["opt_t"] = np.array(self.optimizer.t)

        save_dict["trained_steps"] = np.array(self.trained_steps)
        save_dict["is_trained"] = np.array(self.is_trained)
        save_dict["last_train_loss"] = np.array(self.last_train_loss if self.last_train_loss is not None else -1.0)
        save_dict["last_train_acc"] = np.array(self.last_train_acc if self.last_train_acc is not None else -1.0)

        # Metadatos de arquitectura, para verificar compatibilidad al recargar
        save_dict["n_features"] = np.array(self.n_features)
        save_dict["seq_len"] = np.array(self.seq_len)
        save_dict["d_model"] = np.array(self.d_model)
        save_dict["n_heads"] = np.array(self.n_heads)
        save_dict["n_layers"] = np.array(self.n_layers)
        save_dict["d_ff"] = np.array(self.d_ff)
        save_dict["saved_at"] = np.array(time.time())

        # Escritura "atómica": se guarda en un .tmp y luego se renombra,
        # para no dejar un archivo corrupto si el proceso se interrumpe a mitad de guardado.
        tmp_path = filepath + ".tmp.npz"
        np.savez(tmp_path, **save_dict)
        os.replace(tmp_path, filepath)

    def load_weights(self, filepath):
        """Intenta cargar pesos guardados previamente. Devuelve True si tuvo éxito.
        Si el archivo no existe, o la arquitectura guardada no coincide con la
        configuración actual, o el archivo está corrupto, devuelve False sin
        modificar el modelo (que seguirá con sus pesos inicializados al azar)."""
        if not filepath or not os.path.exists(filepath):
            return False
        try:
            data = np.load(filepath, allow_pickle=False)
            try:
                if (int(data["n_features"]) != self.n_features or
                        int(data["d_model"]) != self.d_model or
                        int(data["n_heads"]) != self.n_heads or
                        int(data["n_layers"]) != self.n_layers or
                        int(data["d_ff"]) != self.d_ff or
                        int(data["seq_len"]) != self.seq_len):
                    print("   ⚠️ El checkpoint guardado no coincide con la arquitectura actual del "
                          "Transformer (cambiaste algún hiperparámetro). Se ignora y se entrena desde cero.")
                    return False

                params = {}
                for key in data.files:
                    if key.startswith("param__"):
                        params[key[len("param__"):]] = data[key]
                self.load_all_params(params)

                self.optimizer.m = {}
                self.optimizer.v = {}
                for key in data.files:
                    if key.startswith("optm__"):
                        self.optimizer.m[key[len("optm__"):]] = data[key]
                    elif key.startswith("optv__"):
                        self.optimizer.v[key[len("optv__"):]] = data[key]
                if "opt_t" in data.files:
                    self.optimizer.t = int(data["opt_t"])

                if "trained_steps" in data.files:
                    self.trained_steps = int(data["trained_steps"])
                if "is_trained" in data.files:
                    self.is_trained = bool(data["is_trained"])
                if "last_train_loss" in data.files:
                    v = float(data["last_train_loss"])
                    self.last_train_loss = v if v >= 0 else None
                if "last_train_acc" in data.files:
                    v = float(data["last_train_acc"])
                    self.last_train_acc = v if v >= 0 else None
                self._loaded_saved_at = float(data["saved_at"]) if "saved_at" in data.files else None
                return True
            finally:
                data.close()
        except Exception as e:
            print(f"   ⚠️ No se pudo cargar el modelo guardado ({e}). Se entrenará desde cero.")
            return False

    def forward(self, X, training=True):
        """X: (B, T, n_features) -> logits (B, 2), probs (B, 2)"""
        B, T, F = X.shape
        embed = X @ self.W_embed + self.b_embed  # (B,T,d_model)
        x = embed + self.pos_encoding[:T][None, :, :]
        self._cache_embed = (X, embed)

        for layer in self.layers:
            x = layer.forward(x, training)

        x_norm = self.ln_final.forward(x)
        pooled = np.mean(x_norm, axis=1)  # (B, d_model) - mean pooling temporal
        self._cache_pool = (x_norm, x.shape[1])
        logits = pooled @ self.W_out + self.b_out
        probs = _softmax(logits, axis=-1)
        return logits, probs

    def backward(self, probs, y_onehot):
        """Backprop completo desde la pérdida de cross-entropy hasta la entrada."""
        B = probs.shape[0]
        d_logits = (probs - y_onehot) / B  # gradiente softmax+CE

        x_norm, T = self._cache_pool
        d_pooled = d_logits @ self.W_out.T
        d_W_out = (x_norm.mean(axis=1)).T @ d_logits
        d_b_out = np.sum(d_logits, axis=0)

        d_x_norm = np.repeat(d_pooled[:, None, :], T, axis=1) / T

        d_x, g_lnf = self.ln_final.backward(d_x_norm)

        grads = {"W_out": d_W_out, "b_out": d_b_out}
        grads.update(g_lnf)

        for layer in reversed(self.layers):
            d_x, g_layer = layer.backward(d_x)
            grads.update(g_layer)

        X, embed = self._cache_embed
        d_embed = d_x  # positional encoding no es entrenable
        F = X.shape[-1]
        d_W_embed = X.reshape(-1, F).T @ d_embed.reshape(-1, self.d_model)
        d_b_embed = np.sum(d_embed, axis=(0, 1))
        grads["W_embed"] = d_W_embed
        grads["b_embed"] = d_b_embed
        return grads

    def train_step(self, X_batch, y_batch_idx):
        """Un paso de entrenamiento: forward + backward + Adam.update"""
        y_onehot = np.zeros((len(y_batch_idx), 2))
        y_onehot[np.arange(len(y_batch_idx)), y_batch_idx] = 1.0
        logits, probs = self.forward(X_batch, training=True)
        eps = 1e-9
        loss = -np.mean(np.sum(y_onehot * np.log(probs + eps), axis=-1))
        preds = np.argmax(probs, axis=-1)
        acc = float(np.mean(preds == np.array(y_batch_idx)))
        grads = self.backward(probs, y_onehot)
        params = self.get_all_params()
        self.optimizer.step(params, grads)
        self.load_all_params(params)
        self.trained_steps += 1
        return loss, acc

    def fit(self, X, y, epochs, batch_size, verbose_prefix="🧠"):
        """Entrena con mini-batches durante `epochs` épocas sobre (X,y) completos."""
        n = len(X)
        if n == 0:
            return
        for epoch in range(epochs):
            idx = np.random.permutation(n)
            X_shuf, y_shuf = X[idx], y[idx]
            losses, accs = [], []
            for i in range(0, n, batch_size):
                xb = X_shuf[i:i + batch_size]
                yb = y_shuf[i:i + batch_size]
                if len(xb) == 0:
                    continue
                loss, acc = self.train_step(xb, yb)
                losses.append(loss)
                accs.append(acc)
            if losses:
                self.last_train_loss = float(np.mean(losses))
                self.last_train_acc = float(np.mean(accs))
            if epochs <= 5 or epoch % max(1, epochs // 5) == 0 or epoch == epochs - 1:
                print(f"   {verbose_prefix} Época {epoch+1}/{epochs} | loss={self.last_train_loss:.4f} | acc={self.last_train_acc:.1%}")
        self.is_trained = True

    def predict_proba(self, X):
        """Inferencia (sin dropout). X: (1, T, n_features) -> probs (1,2)"""
        _, probs = self.forward(X, training=False)
        return probs


class PatternMemory:
    """
    Memoria persistente de patrones de operaciones GANADAS y PERDIDAS
    (equivalente al concepto de "memoria persistente" + "Q-Learning: aprende
    de operaciones ganadas y perdidas"). Guarda, por divisa, la secuencia de
    features que precedió a cada operación real junto con la etiqueta
    derivada del resultado en capital, para poder reforzar al Transformer
    con esas experiencias (experience replay) tanto en la sesión actual
    como en sesiones futuras.
    """

    def __init__(self, symbol):
        self.symbol = symbol
        self.filepath = os.path.join(ConfigGlobal.TRANSFORMER_MODEL_DIR,
                                      f"patterns_{self._safe(symbol)}.npz")
        self.X = []
        self.y = []
        self.resultados = []
        self._load()

    @staticmethod
    def _safe(symbol):
        return "".join(c if (c.isalnum() or c in "-_") else "_" for c in str(symbol))

    def _load(self):
        if not os.path.exists(self.filepath):
            return
        try:
            data = np.load(self.filepath, allow_pickle=False)
            try:
                self.X = list(data["X"]) if "X" in data.files else []
                self.y = list(data["y"]) if "y" in data.files else []
                self.resultados = list(data["resultados"]) if "resultados" in data.files else []
                if self.X:
                    print(f"   🧠 [Memoria] {len(self.X)} patrones previos de operaciones cargados "
                          f"para {self.symbol} (refuerzo tipo Q-Learning).")
            finally:
                data.close()
        except Exception as e:
            print(f"   ⚠️ [Memoria] No se pudo cargar la memoria de patrones: {e}")

    def add(self, feats_seq, label, resultado):
        self.X.append(np.array(feats_seq, dtype=np.float64))
        self.y.append(int(label))
        self.resultados.append(resultado)
        max_n = ConfigGlobal.CAPITAL_PATTERN_MEMORY_MAX
        if len(self.X) > max_n:
            self.X = self.X[-max_n:]
            self.y = self.y[-max_n:]
            self.resultados = self.resultados[-max_n:]

    def save(self):
        if not self.X:
            return
        try:
            os.makedirs(ConfigGlobal.TRANSFORMER_MODEL_DIR, exist_ok=True)
            tmp_path = self.filepath + ".tmp.npz"
            np.savez(tmp_path, X=np.array(self.X), y=np.array(self.y),
                      resultados=np.array(self.resultados))
            os.replace(tmp_path, self.filepath)
        except Exception as e:
            print(f"⚠️ [Memoria] No se pudo guardar la memoria de patrones: {e}")

    def sample_replay(self, n):
        """Devuelve hasta n patrones al azar del historial (experience replay)."""
        if not self.X:
            return None, None
        idx = np.random.choice(len(self.X), size=min(n, len(self.X)), replace=False)
        return np.array([self.X[i] for i in idx]), np.array([self.y[i] for i in idx])

    def stats(self):
        ganadas = sum(1 for r in self.resultados if r == "GANADA")
        perdidas = sum(1 for r in self.resultados if r == "PERDIDA")
        return {"total": len(self.resultados), "ganadas": ganadas, "perdidas": perdidas}


class TransformerSignalEngine:
    """
    Motor que conecta el DeepTransformer con datos reales de mercado:
      - Construye secuencias y etiquetas (sube/baja) a partir de cierres reales
      - Entrena automáticamente al iniciar (≥500 cierres reales si están disponibles)
      - Reentrena cada N ciclos en un hilo en segundo plano (no bloquea la UI)
      - Expone get_signal() -> dict con acción, confianza y probabilidades
      - 🧠 Refuerzo Q-Learning: aprende del resultado REAL (capital) de cada
        operación ejecutada, vía PatternMemory + experience replay
    """
    FEATURE_NAMES = ["ret", "ret_z", "ema_fast_diff", "ema_slow_diff", "rsi_norm", "volat"]

    def __init__(self, tech_analyzer: 'TechnicalIndicatorAnalyzer'):
        self.tech_analyzer = tech_analyzer
        self.seq_len = ConfigGlobal.TRANSFORMER_SEQ_LEN
        self.model = None
        self.lock = threading.Lock()
        self.training_in_progress = False
        self.last_signal = {
            "action": "ESPERAR", "confidence": 0.0, "prob_up": 0.5, "prob_down": 0.5,
            "status": "SIN_ENTRENAR", "trained_steps": 0
        }
        self.cycles_since_train = 0
        self.symbol = None
        self._last_feats_seq = None       # última secuencia de entrada usada en get_signal()
        self.pattern_memory = None        # PatternMemory, creada en initial_train(symbol)

    # ---------------------------------------------------------------
    # Construcción de features a partir de precios reales (closes)
    # ---------------------------------------------------------------
    def _build_features(self, closes):
        closes = np.array(closes, dtype=np.float64)
        n = len(closes)
        if n < self.seq_len + 5:
            return None
        rets = np.diff(closes) / (closes[:-1] + 1e-12)
        rets = np.concatenate([[0.0], rets])
        ema_fast = np.array(MathUtils.ema(list(closes), 8))
        ema_slow = np.array(MathUtils.ema(list(closes), 21))
        ema_fast_diff = (closes - ema_fast) / (closes + 1e-12)
        ema_slow_diff = (closes - ema_slow) / (closes + 1e-12)

        rsi_series = []
        period = 14
        for i in range(n):
            window = list(closes[max(0, i - period):i + 1])
            r = self.tech_analyzer.compute_rsi(window, period=min(period, max(2, len(window) - 1)))
            rsi_series.append(r.get("rsi", 50.0))
        rsi_norm = (np.array(rsi_series) - 50.0) / 50.0

        roll = 10
        ret_z = np.zeros(n)
        for i in range(n):
            w = rets[max(0, i - roll):i + 1]
            mu, sd = np.mean(w), np.std(w) + 1e-9
            ret_z[i] = (rets[i] - mu) / sd

        volat = np.zeros(n)
        for i in range(n):
            w = rets[max(0, i - roll):i + 1]
            volat[i] = np.std(w)

        feats = np.stack([rets, ret_z, ema_fast_diff, ema_slow_diff, rsi_norm, volat], axis=-1)
        feats = np.nan_to_num(feats, nan=0.0, posinf=0.0, neginf=0.0)
        # Normalización por feature (z-score global de la ventana disponible)
        mu = feats.mean(axis=0, keepdims=True)
        sd = feats.std(axis=0, keepdims=True) + 1e-9
        feats_norm = (feats - mu) / sd
        return feats_norm

    def _build_dataset(self, closes):
        """Construye (X, y) supervisados: X=secuencia de seq_len pasos, y=1 si el
        siguiente cierre sube respecto al actual, 0 si baja/igual."""
        feats = self._build_features(closes)
        if feats is None:
            return None, None
        closes = np.array(closes, dtype=np.float64)
        n = len(feats)
        X, y = [], []
        for i in range(self.seq_len, n - 1):
            seq = feats[i - self.seq_len:i]
            label = 1 if closes[i + 1] > closes[i] else 0
            X.append(seq)
            y.append(label)
        if not X:
            return None, None
        return np.array(X), np.array(y)

    # ---------------------------------------------------------------
    # 💾 Ruta del checkpoint por símbolo (un modelo por divisa)
    # ---------------------------------------------------------------
    def _model_filepath(self, symbol):
        safe_symbol = "".join(c if (c.isalnum() or c in "-_") else "_" for c in str(symbol))
        return os.path.join(ConfigGlobal.TRANSFORMER_MODEL_DIR, f"transformer_{safe_symbol}.npz")

    # ---------------------------------------------------------------
    # Entrenamiento inicial (bloqueante, una sola vez al arrancar)
    # ---------------------------------------------------------------
    def initial_train(self, symbol):
        self.symbol = symbol
        self.pattern_memory = PatternMemory(symbol)
        print("\n" + "="*70)
        print("🧠 TRANSFORMER PROFUNDO — ENTRENAMIENTO INICIAL")
        print(f"   Arquitectura: {ConfigGlobal.TRANSFORMER_N_LAYERS} capas, "
              f"{ConfigGlobal.TRANSFORMER_N_HEADS} cabezas, d_model={ConfigGlobal.TRANSFORMER_D_MODEL}, "
              f"d_ff={ConfigGlobal.TRANSFORMER_D_FF}, dropout={ConfigGlobal.TRANSFORMER_DROPOUT}")
        print("="*70)
        closes = UnifiedForexDataProvider.get_real_closes(symbol, candles=ConfigGlobal.TRANSFORMER_MIN_CLOSES)
        if len(closes) < ConfigGlobal.TRANSFORMER_MIN_CLOSES_FLOOR:
            print(f"   ⚠️ Sólo {len(closes)} cierres reales disponibles (mínimo deseado "
                  f"{ConfigGlobal.TRANSFORMER_MIN_CLOSES}). Se entrenará con lo disponible "
                  f"y se reentrenará automáticamente cuando haya más historial.")
        else:
            print(f"   ✅ {len(closes)} cierres reales (1m) descargados de Yahoo Finance para {symbol}")

        X, y = self._build_dataset(closes)
        self.model = DeepTransformer(n_features=len(self.FEATURE_NAMES))

        # --- 💾 Intentar cargar un modelo ya entrenado en una sesión anterior ---
        model_path = self._model_filepath(symbol)
        loaded = self.model.load_weights(model_path)
        fine_tune_only = False
        if loaded:
            age_hours = None
            if self.model._loaded_saved_at:
                age_hours = (time.time() - self.model._loaded_saved_at) / 3600.0
            if age_hours is not None and age_hours <= ConfigGlobal.TRANSFORMER_MODEL_MAX_AGE_HOURS:
                fine_tune_only = True
                print(f"   💾 Modelo guardado encontrado para {symbol} (antigüedad: {age_hours:.1f}h, "
                      f"{self.model.trained_steps} pasos ya entrenados). Se omite el entrenamiento "
                      f"inicial completo y se hace sólo un ajuste fino breve.")
            else:
                age_str = f"{age_hours:.1f}h" if age_hours is not None else "desconocida"
                print(f"   💾 Modelo guardado encontrado para {symbol} pero su antigüedad ({age_str}) "
                      f"supera el límite configurado ({ConfigGlobal.TRANSFORMER_MODEL_MAX_AGE_HOURS}h). "
                      f"Se continúa entrenando desde esos pesos con el ciclo completo de épocas.")
        else:
            print(f"   🆕 No se encontró un modelo guardado para {symbol}. Se entrenará desde cero.")

        if X is None or len(X) < 10:
            if loaded:
                # Tenemos pesos previos utilizables aunque ahora no haya datos suficientes
                self.last_signal["status"] = "ENTRENADO" if self.model.is_trained else "CALENTANDO"
                print("   ℹ️ Datos insuficientes para reentrenar ahora mismo; se usa el modelo cargado tal cual.")
            else:
                print("   ⚠️ Datos insuficientes para entrenamiento inicial completo. "
                      "El Transformer operará en modo 'calentamiento' hasta acumular historial real.")
                self.last_signal["status"] = "CALENTANDO"
            print("="*70 + "\n")
            return

        epochs = ConfigGlobal.TRANSFORMER_EPOCHS_FINE_TUNE if fine_tune_only else ConfigGlobal.TRANSFORMER_EPOCHS_INIT
        prefix = "🧠 [AJUSTE FINO]" if fine_tune_only else "🧠 [INICIAL]"
        print(f"   📦 Dataset supervisado: {len(X)} secuencias (seq_len={self.seq_len})")
        self.model.fit(X, y, epochs=epochs,
                        batch_size=ConfigGlobal.TRANSFORMER_BATCH_SIZE,
                        verbose_prefix=prefix)
        self.last_signal["status"] = "ENTRENADO"
        print(f"   ✅ Entrenamiento {'(ajuste fino) ' if fine_tune_only else ''}completo | "
              f"loss={self.model.last_train_loss:.4f} | acc={self.model.last_train_acc:.1%}")

        # --- 💾 Guardar pesos tras el entrenamiento (inicial o ajuste fino) ---
        try:
            self.model.save_weights(model_path)
            print(f"   💾 Pesos del modelo guardados en: {model_path}")
        except Exception as e:
            print(f"   ⚠️ No se pudieron guardar los pesos del modelo: {e}")
        print("="*70 + "\n")

    # ---------------------------------------------------------------
    # Reentrenamiento periódico en segundo plano (no bloquea la UI)
    # ---------------------------------------------------------------
    def maybe_retrain_async(self, symbol):
        self.cycles_since_train += 1
        if self.cycles_since_train < ConfigGlobal.TRANSFORMER_RETRAIN_CICLOS:
            return
        if self.training_in_progress:
            return
        self.cycles_since_train = 0
        thread = threading.Thread(target=self._retrain_worker, args=(symbol,), daemon=True)
        thread.start()

    def _retrain_worker(self, symbol):
        self.training_in_progress = True
        try:
            closes = UnifiedForexDataProvider.get_real_closes(symbol, candles=ConfigGlobal.TRANSFORMER_MIN_CLOSES)
            X, y = self._build_dataset(closes)
            if X is None or len(X) < 10 or self.model is None:
                return
            print(f"\n🔄 [Transformer] Reentrenamiento automático en segundo plano "
                  f"({len(X)} secuencias, {ConfigGlobal.TRANSFORMER_EPOCHS_RETRAIN} épocas)...")
            with self.lock:
                self.model.fit(X, y, epochs=ConfigGlobal.TRANSFORMER_EPOCHS_RETRAIN,
                                batch_size=ConfigGlobal.TRANSFORMER_BATCH_SIZE,
                                verbose_prefix="🔄 [REENTRENO]")
                model_path = self._model_filepath(symbol)
                try:
                    self.model.save_weights(model_path)
                except Exception as e:
                    print(f"⚠️ [Transformer] No se pudieron guardar los pesos tras el reentrenamiento: {e}")
            print(f"✅ [Transformer] Reentrenamiento completo | loss={self.model.last_train_loss:.4f} | "
                  f"acc={self.model.last_train_acc:.1%}")
            print(f"💾 [Transformer] Pesos actualizados guardados en: {model_path}\n")
        except Exception as e:
            print(f"⚠️ [Transformer] Error en reentrenamiento: {e}")
        finally:
            self.training_in_progress = False

    # ---------------------------------------------------------------
    # Inferencia: produce la señal del Transformer para el ciclo actual
    # ---------------------------------------------------------------
    def get_signal(self, closes):
        if self.model is None:
            return self.last_signal
        feats = self._build_features(closes)
        if feats is None or len(feats) < self.seq_len:
            self.last_signal.update({"status": "CALENTANDO"})
            return self.last_signal
        seq = feats[-self.seq_len:]
        self._last_feats_seq = seq  # guardada para poder reforzar luego con el resultado real (capital)
        X = seq[None, :, :]
        try:
            with self.lock:
                probs = self.model.predict_proba(X)
        except Exception as e:
            print(f"⚠️ [Transformer] Error en inferencia: {e}")
            return self.last_signal
        prob_down, prob_up = float(probs[0, 0]), float(probs[0, 1])
        confidence = abs(prob_up - prob_down)
        if not self.model.is_trained:
            action = "ESPERAR"
            status = "CALENTANDO"
        elif prob_up > prob_down and confidence >= (ConfigGlobal.TRANSFORMER_CONF_MIN - 0.5) * 2:
            action = "COMPRA"
            status = "ENTRENADO"
        elif prob_down > prob_up and confidence >= (ConfigGlobal.TRANSFORMER_CONF_MIN - 0.5) * 2:
            action = "VENTA"
            status = "ENTRENADO"
        else:
            action = "ESPERAR"
            status = "ENTRENADO"
        self.last_signal = {
            "action": action,
            "confidence": float(min(0.99, confidence)),
            "prob_up": prob_up,
            "prob_down": prob_down,
            "status": status,
            "trained_steps": self.model.trained_steps
        }
        return self.last_signal

    # ---------------------------------------------------------------
    # 🧠 REFUERZO Q-LEARNING: aprender del resultado REAL de una
    #     operación (GANADA/PERDIDA), medido por el capital real vía OCR
    # ---------------------------------------------------------------
    def get_last_feats_seq(self):
        """Secuencia de features que produjo la última señal (para asociarla
        a la operación que se ejecute a partir de esa señal)."""
        return self._last_feats_seq

    def reinforce_from_outcome(self, feats_seq, label, resultado):
        """
        Refuerza el modelo con el desenlace REAL de una operación:
          - feats_seq: secuencia (seq_len, n_features) que precedió a la operación
          - label: 1 si el precio realmente subió (según el resultado en capital
                   y la dirección operada), 0 si bajó
          - resultado: "GANADA" o "PERDIDA" (para estadística/memoria)

        Guarda la experiencia en memoria persistente (PatternMemory) y aplica
        un paso de entrenamiento tipo "experience replay": combina la muestra
        nueva con una repetición aleatoria de patrones pasados, para reforzar
        aprendizaje sin sobreajustar a la última operación ni olvidar el resto.
        """
        if not ConfigGlobal.CAPITAL_REINFORCE_ENABLED or self.model is None or feats_seq is None:
            return False
        if self.pattern_memory is None:
            self.pattern_memory = PatternMemory(self.symbol or "DEFAULT")

        self.pattern_memory.add(feats_seq, label, resultado)
        self.pattern_memory.save()

        if len(self.pattern_memory.X) < ConfigGlobal.CAPITAL_REINFORCE_MIN_BATCH:
            return False  # aún no hay suficiente experiencia para un mini-batch estable

        try:
            n_replay = min(ConfigGlobal.CAPITAL_REINFORCE_MAX_REPLAY, len(self.pattern_memory.X))
            X_batch, y_batch = self.pattern_memory.sample_replay(n_replay)
            if X_batch is None:
                return False
            with self.lock:
                loss, acc = self.model.train_step(X_batch, y_batch)
                try:
                    self.model.save_weights(self._model_filepath(self.symbol))
                except Exception as e:
                    print(f"⚠️ [Refuerzo] No se pudieron guardar los pesos tras el refuerzo: {e}")
            print(f"🧠 [Refuerzo Q-Learning] Operación {resultado} incorporada | "
                  f"replay={n_replay} patrones | loss={loss:.4f} | acc={acc:.1%}")
            return True
        except Exception as e:
            print(f"⚠️ [Refuerzo] Error aplicando refuerzo por resultado real: {e}")
            return False

# =============================================================================
# 📦 ESTRUCTURAS DE DATOS (incorporado de SAOTT156)
# =============================================================================

from dataclasses import dataclass, field as _dc_field

@dataclass
class MarketState:
    price: float = 0.0
    volume: float = 0.0
    volatility: float = 0.02
    spread: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    trend_1m: float = 0.0
    momentum: float = 0.0
    timestamp: datetime = _dc_field(default_factory=datetime.now)

    def to_dict(self):
        return {
            'price': self.price, 'volume': self.volume, 'volatility': self.volatility,
            'spread': self.spread, 'trend_1m': self.trend_1m, 'momentum': self.momentum,
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class TradingSignal:
    action: str
    confidence: float = 0.5
    alpha: float = 0.0
    risk: float = 0.0
    cost: float = 0.0
    size: float = 0.0
    metadata: dict = _dc_field(default_factory=dict)
    timestamp: datetime = _dc_field(default_factory=datetime.now)

    def is_valid(self):
        return self.confidence >= 0.5 and self.action in ['BUY', 'SELL', 'COMPRA', 'VENTA']

# =============================================================================
# 🌐 PROVEEDOR UNIFICADO DE DATOS FOREX (MÚLTIPLES FUENTES GRATUITAS)
# =============================================================================
# Ahora con integración de YahooFinanceCore como fuente primaria con caché
# =============================================================================

class UnifiedForexDataProvider:
    """Obtiene precio real de divisas con failover automático entre múltiples APIs gratuitas.
       Utiliza YahooFinanceCore como fuente principal (con caché) y luego otras APIs."""

    # Mapeo de símbolos con =X a códigos ISO para las APIs
    SYMBOL_MAP = {
        "EURUSD=X": {"base": "EUR", "quote": "USD"},
        "GBPUSD=X": {"base": "GBP", "quote": "USD"},
        "USDJPY=X": {"base": "USD", "quote": "JPY"},
        "USDCHF=X": {"base": "USD", "quote": "CHF"},
        "AUDUSD=X": {"base": "AUD", "quote": "USD"},
        "USDCAD=X": {"base": "USD", "quote": "CAD"},
        "NZDUSD=X": {"base": "NZD", "quote": "USD"},
        "EURGBP=X": {"base": "EUR", "quote": "GBP"},
    }

    _cache = {}
    _cache_time = {}
    CACHE_TTL = 0.5  # segundos (actualización muy frecuente)
    _yf_core = YahooFinanceCore() if YF_AVAILABLE else None

    @classmethod
    def get_current_price(cls, symbol: str) -> float:
        """Devuelve el precio actual real de la divisa o None si todas las fuentes fallan."""
        now = time.time()
        if symbol in cls._cache and (now - cls._cache_time.get(symbol, 0)) < cls.CACHE_TTL:
            return cls._cache[symbol]

        mapping = cls.SYMBOL_MAP.get(symbol)
        if not mapping:
            return None
        base = mapping["base"]
        quote = mapping["quote"]
        price = None

        # 1. Yahoo Finance usando YahooFinanceCore (con caché interno)
        if cls._yf_core is not None:
            try:
                price = cls._yf_core.get_price_cached(symbol)
                if price and price > 0:
                    cls._cache[symbol] = float(price)
                    cls._cache_time[symbol] = now
                    return float(price)
            except Exception:
                pass

        # 2. ExchangeRate.host (gratuito)
        try:
            if base == "USD":
                url = f"https://api.exchangerate.host/latest?base=USD&symbols={quote}"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    price = data.get('rates', {}).get(quote)
            else:
                # Obtener base->USD y luego USD->quote
                url_base = f"https://api.exchangerate.host/latest?base={base}&symbols=USD"
                resp_base = requests.get(url_base, timeout=5)
                if resp_base.status_code == 200:
                    data_base = resp_base.json()
                    rate_base_usd = data_base.get('rates', {}).get('USD')
                    if rate_base_usd:
                        url_quote = f"https://api.exchangerate.host/latest?base=USD&symbols={quote}"
                        resp_quote = requests.get(url_quote, timeout=5)
                        if resp_quote.status_code == 200:
                            data_quote = resp_quote.json()
                            rate_usd_quote = data_quote.get('rates', {}).get(quote)
                            if rate_usd_quote:
                                price = rate_usd_quote / rate_base_usd
            if price:
                cls._cache[symbol] = float(price)
                cls._cache_time[symbol] = now
                return float(price)
        except Exception:
            pass

        # 3. Frankfurter (gratuito)
        try:
            url = f"https://api.frankfurter.app/latest?from={base}&to={quote}"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                price = data.get('rates', {}).get(quote)
                if price:
                    cls._cache[symbol] = float(price)
                    cls._cache_time[symbol] = now
                    return float(price)
        except Exception:
            pass

        # 4. ExchangeRate-API (gratuito, sin clave)
        try:
            url = f"https://api.exchangerate-api.com/v4/latest/{base}"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                price = data.get('rates', {}).get(quote)
                if price:
                    cls._cache[symbol] = float(price)
                    cls._cache_time[symbol] = now
                    return float(price)
        except Exception:
            pass

        # 5. CurrencyAPI (demo pública gratuita)
        try:
            api_key = "cur_live_7Z3mX9kL2pQ4rT1wY5nA8vF6cH0jM"
            url = f"https://api.currencyapi.com/v3/latest?apikey={api_key}&base_currency={base}&currencies={quote}"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                price = data.get('data', {}).get(quote, {}).get('value')
                if price:
                    cls._cache[symbol] = float(price)
                    cls._cache_time[symbol] = now
                    return float(price)
        except Exception:
            pass

        # Si todas fallaron, devolvemos el último precio en caché (aunque caducado) para no interrumpir
        if symbol in cls._cache:
            return cls._cache[symbol]
        return None

    @classmethod
    def get_real_closes(cls, symbol: str, candles: int = 100):
        """Devuelve cierres reales recientes (1m) desde Yahoo Finance. Lista vacía si no disponible."""
        if cls._yf_core is not None:
            try:
                closes = cls._yf_core.get_closes(symbol, candles=candles)
                if closes:
                    return [float(c) for c in closes]
            except Exception:
                pass
        return []

    @classmethod
    def get_real_last_candle(cls, symbol: str):
        """Devuelve la última vela real OHLCV (1m) desde Yahoo Finance, o None."""
        if cls._yf_core is not None:
            try:
                return cls._yf_core.get_last_candle(symbol)
            except Exception:
                pass
        return None

# =============================================================================
# 🕐 SISTEMA DE TEMPORIZACIÓN AVANZADO (COMPLETO ORIGINAL)
# =============================================================================

class AdvancedTemporizador:
    def __init__(self, tiempo_vela_segundos=ConfigGlobal.TIEMPO_VELA_SEGUNDOS):
        self.tiempo_vela = tiempo_vela_segundos
        self.timeframes = [60, 300, 900]
        self.historial = deque(maxlen=100)
        self.precision_ns = 0
        self._calibrar_precision()
        self._calcular_proximo_cierre()
        print(f"⏰ Temporizador Avanzado: {tiempo_vela_segundos}s")
        print(f"   Precisión: {self.precision_ns}ns")

    def _calibrar_precision(self):
        tiempos = []
        for _ in range(10):
            start = time.perf_counter_ns()
            time.sleep(0.001)
            end = time.perf_counter_ns()
            tiempos.append(end - start)
        self.precision_ns = int(np.mean(tiempos))

    def _calcular_proximo_cierre(self):
        ahora = datetime.now()
        if self.tiempo_vela == 60:
            self.proximo_cierre = (ahora + timedelta(minutes=1)).replace(second=0, microsecond=0)
        elif self.tiempo_vela == 300:
            minutos_actuales = ahora.minute
            minutos_proximos = ((minutos_actuales // 5) + 1) * 5
            if minutos_proximos == 60:
                self.proximo_cierre = (ahora + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            else:
                self.proximo_cierre = ahora.replace(minute=minutos_proximos, second=0, microsecond=0)
        else:
            epoch_seconds = int(ahora.timestamp())
            next_epoch = ((epoch_seconds // self.tiempo_vela) + 1) * self.tiempo_vela
            self.proximo_cierre = datetime.fromtimestamp(next_epoch)
        self.ultimo_cierre = self.proximo_cierre - timedelta(seconds=self.tiempo_vela)
        self.historial.append(self.proximo_cierre)

    def actualizar(self):
        ahora = datetime.now()
        self.segundos_restantes = (self.proximo_cierre - ahora).total_seconds()
        if ahora >= self.proximo_cierre:
            return self._procesar_cierre()
        return False

    def _procesar_cierre(self):
        ahora = datetime.now()
        self.historial.append(ahora)
        desviacion = (ahora - self.proximo_cierre).total_seconds() * 1000
        if abs(desviacion) > 50:
            print(f"⚠️ Desviación: {desviacion:.1f}ms")
        self._calcular_proximo_cierre()
        return True

    def get_tiempo_restante(self):
        ahora = datetime.now()
        segundos = int((self.proximo_cierre - ahora).total_seconds())
        return max(0, segundos)

    def get_tiempo_formateado(self):
        segundos = self.get_tiempo_restante()
        minutos = segundos // 60
        segs = segundos % 60
        return f"{minutos:02d}:{segs:02d}"

    def get_proximo_cierre_str(self):
        return self.proximo_cierre.strftime('%H:%M:%S')

    def get_hora_sistema(self):
        return datetime.now().strftime('%H:%M:%S.%f')[:-3]

    def get_sincronizacion_stats(self):
        if len(self.historial) < 2:
            return {"precisión_ns": self.precision_ns, "desviacion_promedio_ms": 0, "desviacion_max_ms": 0, "cierres_registrados": len(self.historial)}
        desviaciones = []
        for i in range(1, len(self.historial)):
            esperado = self.historial[i-1] + timedelta(seconds=self.tiempo_vela)
            real = self.historial[i]
            desviacion = (real - esperado).total_seconds() * 1000
            desviaciones.append(desviacion)
        return {
            "precisión_ns": self.precision_ns,
            "desviacion_promedio_ms": np.mean(np.abs(desviaciones)) if desviaciones else 0,
            "desviacion_max_ms": max(np.abs(desviaciones)) if desviaciones else 0,
            "cierres_registrados": len(self.historial)
        }

# =============================================================================
# 📊 MÓDULO DE PRICE ACTION COMPLETO (ORIGINAL, SIN MODIFICACIONES)
# =============================================================================

class PriceActionAnalyzer:
    def __init__(self):
        self.sct = mss.mss()
        self.velas_historial = deque(maxlen=100)
        self.soportes_resistencias = []
        self.patrones_detectados = []
        print("✅ Price Action Analyzer con Visualización inicializado")
        print(f"   Métodos: BOS, Pin Bar, Falsos Rompimientos, S/R, Smart Money")

    def capturar_pantalla(self):
        img = self.sct.grab(ConfigGlobal.MONITOR)
        frame = np.array(img)
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    def detectar_velas_avanzado(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 30, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        velas_contornos = []
        frame_con_contornos = frame.copy()
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if 20 < h < 250 and 3 < w < 30:
                open_y = y + (h // 3)
                close_y = y + (h * 2 // 3)
                es_alcista = open_y > close_y  # en coords de imagen, close más arriba = subida
                color = (0, 255, 0) if es_alcista else (0, 0, 255)
                cv2.rectangle(frame_con_contornos, (x, y), (x+w, y+h), color, 1)
                velas_contornos.append({
                    "x": x, "y": y, "w": w, "h": h,
                    "high": y, "low": y + h,
                    "open": open_y, "close": close_y,
                    "cuerpo": abs(open_y - close_y),
                    "mecha_superior": 0, "mecha_inferior": 0,
                    "color": "VERDE" if es_alcista else "ROJO",
                    "tipo": "contorno"
                })
        h, w, _ = frame.shape
        velas_zona = []
        paso = w // ConfigGlobal.VELAS_A_ANALIZAR
        for i in range(ConfigGlobal.VELAS_A_ANALIZAR):
            x1 = i * paso
            x2 = x1 + paso
            zona = frame[:, x1:x2]
            gris = cv2.cvtColor(zona, cv2.COLOR_BGR2GRAY)
            _, binaria = cv2.threshold(gris, 50, 255, cv2.THRESH_BINARY)
            ys = np.where(binaria > 0)[0]
            if len(ys) == 0:
                continue
            high = min(ys)
            low = max(ys)
            open_ = ys[len(ys)//3]
            close = ys[len(ys)*2//3]
            velas_zona.append({
                "x": x1, "y": high, "w": paso, "h": low - high,
                "open": open_, "close": close, "high": high, "low": low,
                "cuerpo": abs(open_ - close),
                "color": "VERDE" if close > open_ else "ROJO",
                "tipo": "zona"
            })
        velas_validadas = []
        if velas_contornos:
            velas_validadas = velas_contornos
        elif velas_zona and len(velas_zona) > 5:
            velas_validadas = velas_zona
        else:
            velas_validadas = self._crear_velas_simuladas(frame)
        velas_validadas = self._asegurar_coordenadas(velas_validadas, frame)
        velas_validadas = sorted(velas_validadas, key=lambda v: v.get("x", 0))
        if velas_validadas:
            self.velas_historial.append({
                "timestamp": datetime.now(),
                "velas": velas_validadas,
                "count": len(velas_validadas)
            })
        return velas_validadas, frame_con_contornos

    def _crear_velas_simuladas(self, frame):
        """Fallback EN VIVO: si la visión por contornos no detecta velas en pantalla,
        se reconstruyen las últimas N velas con datos REALES (Yahoo Finance) de la
        divisa activa, en lugar de generar valores aleatorios."""
        h, w = frame.shape[:2]
        num_velas = ConfigGlobal.VELAS_A_ANALIZAR
        paso = w // num_velas
        velas_reales = []
        symbol = getattr(ConfigGlobal, "DIVISA_ACTIVA", None)
        closes = UnifiedForexDataProvider.get_real_closes(symbol, candles=num_velas) if symbol else []
        if not closes or len(closes) < 2:
            # Sin datos reales disponibles: no se inventan velas, se devuelve lista vacía
            return []
        # Normalizar precios reales a coordenadas de pixel para mantener compatibilidad
        # con el resto del pipeline visual (que trabaja en coordenadas y/altura).
        cmin, cmax = min(closes), max(closes)
        rango = (cmax - cmin) or (cmax * 0.0001 or 1.0)
        margen = int(h * 0.1)
        alto_util = h - 2 * margen
        for i, _ in enumerate(range(num_velas)):
            idx = min(i, len(closes) - 1)
            idx_prev = max(0, idx - 1)
            x = i * paso
            precio_open = closes[idx_prev]
            precio_close = closes[idx]
            y_open = margen + int(alto_util * (1 - (precio_open - cmin) / rango))
            y_close = margen + int(alto_util * (1 - (precio_close - cmin) / rango))
            high = min(y_open, y_close)
            low = max(y_open, y_close)
            velas_reales.append({
                "x": x, "y": high, "w": paso, "h": max(1, low - high),
                "open": y_open, "close": y_close, "high": high, "low": low,
                "precio_open": precio_open, "precio_close": precio_close,
                "cuerpo": abs(y_open - y_close),
                "color": "VERDE" if precio_close >= precio_open else "ROJO",
                "tipo": "real_yahoo"
            })
        return velas_reales

    def _asegurar_coordenadas(self, velas, frame):
        h, w = frame.shape[:2]
        velas_con_coordenadas = []
        for i, vela in enumerate(velas):
            vela_modificada = vela.copy()
            if "x" not in vela_modificada:
                vela_modificada["x"] = i * (w // max(1, len(velas)))
            if "w" not in vela_modificada:
                vela_modificada["w"] = w // ConfigGlobal.VELAS_A_ANALIZAR
            if "y" not in vela_modificada and "high" in vela_modificada:
                vela_modificada["y"] = vela_modificada["high"]
            elif "y" not in vela_modificada:
                vela_modificada["y"] = h // 2
            if "h" not in vela_modificada:
                if "high" in vela_modificada and "low" in vela_modificada:
                    vela_modificada["h"] = vela_modificada["low"] - vela_modificada["high"]
                else:
                    vela_modificada["h"] = 100
            vela_modificada["h"] = max(10, vela_modificada["h"])
            velas_con_coordenadas.append(vela_modificada)
        return velas_con_coordenadas

    def analizar_bos(self, velas):
        if len(velas) < 8:
            return []
        señales = []
        prev_high = min([v.get("high", 0) for v in velas[:-4]])
        prev_low = max([v.get("low", 1000) for v in velas[:-4]])
        last_high = velas[-1].get("high", 0)
        last_low = velas[-1].get("low", 1000)
        if last_high < prev_high:
            señales.append({"tipo": "BOS_BAJISTA", "texto": "📉 BOS BAJISTA (Break of Structure)", "fuerza": 2.0, "accion": "VENTA", "metodologia": "Price Action"})
        if last_low > prev_low:
            señales.append({"tipo": "BOS_ALCISTA", "texto": "📈 BOS ALCISTA (Break of Structure)", "fuerza": 2.0, "accion": "COMPRA", "metodologia": "Price Action"})
        if len(velas) >= 10:
            highs = [v.get("high", 0) for v in velas[-5:]]
            lows = [v.get("low", 1000) for v in velas[-5:]]
            if all(highs[i] < highs[i-1] for i in range(1, 5)):
                señales.append({"tipo": "BOS_BAJISTA_CONFIRMADO", "texto": "📉📉 BOS BAJISTA CONFIRMADO", "fuerza": 2.5, "accion": "VENTA", "metodologia": "Price Action"})
            if all(lows[i] > lows[i-1] for i in range(1, 5)):
                señales.append({"tipo": "BOS_ALCISTA_CONFIRMADO", "texto": "📈📈 BOS ALCISTA CONFIRMADO", "fuerza": 2.5, "accion": "COMPRA", "metodologia": "Price Action"})
        return señales

    def detectar_pinbar_avanzado(self, vela):
        if not isinstance(vela, dict):
            return None
        high = vela.get("high", 0)
        low = vela.get("low", 1000)
        open_ = vela.get("open", 0)
        close = vela.get("close", 0)
        altura = high - low
        if altura < 30:
            return None
        cuerpo = abs(close - open_)
        mecha_superior = high - max(open_, close)
        mecha_inferior = min(open_, close) - low
        if cuerpo < altura * 0.3:
            if mecha_inferior > cuerpo * 2 and mecha_superior < cuerpo:
                return {"tipo": "PINBAR_ALCISTA", "texto": "📍 PIN BAR ALCISTA (Hammer)", "fuerza": 1.5, "accion": "COMPRA", "metodologia": "Price Action"}
            elif mecha_superior > cuerpo * 2 and mecha_inferior < cuerpo:
                return {"tipo": "PINBAR_BAJISTA", "texto": "📍 PIN BAR BAJISTA (Shooting Star)", "fuerza": 1.5, "accion": "VENTA", "metodologia": "Price Action"}
        if cuerpo < altura * 0.1:
            return {"tipo": "DOJI", "texto": "⚖️ DOJI (Indecisión)", "fuerza": 0.5, "accion": "NEUTRAL", "metodologia": "Price Action"}
        return None

    def calcular_soporte_resistencia(self, velas):
        if len(velas) < 10:
            return [], []
        highs = [v.get("high", 0) for v in velas]
        lows = [v.get("low", 1000) for v in velas]
        closes = [v.get("close", 0) for v in velas]
        all_prices = highs + lows + closes
        hist, bins = np.histogram(all_prices, bins=20)
        soportes = []
        resistencias = []
        for i in range(1, len(hist)-1):
            if hist[i] > hist[i-1] and hist[i] > hist[i+1]:
                if bins[i] < np.mean(all_prices):
                    soportes.append(float(bins[i]))
                else:
                    resistencias.append(float(bins[i]))
        soportes = self._filtrar_niveles(soportes, 10)
        resistencias = self._filtrar_niveles(resistencias, 10)
        self.soportes_resistencias = {"soportes": soportes[:3], "resistencias": resistencias[:3], "timestamp": datetime.now()}
        return soportes[:3], resistencias[:3]

    def _filtrar_niveles(self, niveles, tolerancia):
        if not niveles:
            return []
        niveles.sort()
        filtrados = [niveles[0]]
        for nivel in niveles[1:]:
            if abs(nivel - filtrados[-1]) > tolerancia:
                filtrados.append(nivel)
        return filtrados

    def detectar_falso_rompimiento(self, velas, soportes, resistencias):
        if len(velas) < 3 or not soportes or not resistencias:
            return []
        señales = []
        ultima_vela = velas[-1]
        penultima_vela = velas[-2] if len(velas) >= 2 else None
        if not penultima_vela:
            return señales
        for resistencia in resistencias:
            if (penultima_vela.get("high", 0) < resistencia and 
                ultima_vela.get("high", 0) > resistencia and
                ultima_vela.get("close", 0) < resistencia):
                señales.append({"tipo": "FALSO_ROMPIMIENTO_ARRIBA", "texto": "⚠️ FALSO ROMPIMIENTO RESISTENCIA", "fuerza": 1.8, "accion": "VENTA", "metodologia": "Price Action", "nivel": resistencia})
                break
        for soporte in soportes:
            if (penultima_vela.get("low", 1000) > soporte and
                ultima_vela.get("low", 1000) < soporte and
                ultima_vela.get("close", 0) > soporte):
                señales.append({"tipo": "FALSO_ROMPIMIENTO_ABAJO", "texto": "⚠️ FALSO ROMPIMIENTO SOPORTE", "fuerza": 1.8, "accion": "COMPRA", "metodologia": "Price Action", "nivel": soporte})
                break
        return señales

    def analizar_smart_money(self, velas):
        if len(velas) < 20:
            return []
        señales = []
        velas_altas = sorted(velas[-10:], key=lambda v: v.get("high", 0))
        velas_bajas = sorted(velas[-10:], key=lambda v: v.get("low", 1000))
        if len(velas_bajas) >= 3:
            bloque_alcista = velas_bajas[0]
            if (bloque_alcista.get("close", 0) > bloque_alcista.get("open", 0) and
                all(v.get("low", 1000) > bloque_alcista.get("low", 1000) for v in velas[-3:])):
                señales.append({"tipo": "ORDER_BLOCK_ALCISTA", "texto": "🟢 BLOQUE DE ÓRDENES ALCISTA (Smart Money)", "fuerza": 2.2, "accion": "COMPRA", "metodologia": "Smart Money Concepts"})
        if len(velas_altas) >= 3:
            bloque_bajista = velas_altas[-1]
            if (bloque_bajista.get("close", 0) < bloque_bajista.get("open", 0) and
                all(v.get("high", 0) < bloque_bajista.get("high", 0) for v in velas[-3:])):
                señales.append({"tipo": "ORDER_BLOCK_BAJISTA", "texto": "🔴 BLOQUE DE ÓRDENES BAJISTA (Smart Money)", "fuerza": 2.2, "accion": "VENTA", "metodologia": "Smart Money Concepts"})
        if len(velas) >= 3:
            v1, v2, v3 = velas[-3], velas[-2], velas[-1]
            gap = self._detectar_fvg(v1, v2, v3)
            if gap:
                señales.append(gap)
        return señales

    def _detectar_fvg(self, v1, v2, v3):
        if (v2.get("low", 1000) > v1.get("high", 0) and v3.get("low", 1000) > v1.get("high", 0)):
            return {"tipo": "FVG_ALCISTA", "texto": "📊 FAIR VALUE GAP ALCISTA", "fuerza": 1.3, "accion": "COMPRA", "metodologia": "Smart Money Concepts"}
        if (v2.get("high", 0) < v1.get("low", 1000) and v3.get("high", 0) < v1.get("low", 1000)):
            return {"tipo": "FVG_BAJISTA", "texto": "📊 FAIR VALUE GAP BAJISTA", "fuerza": 1.3, "accion": "VENTA", "metodologia": "Smart Money Concepts"}
        return None

    def dibujar_temporizador_en_vela(self, frame, velas_contornos, temporizador):
        if not velas_contornos:
            return frame
        ultima_vela = velas_contornos[-1]
        for coord in ["x", "y", "w", "h"]:
            if coord not in ultima_vela:
                ultima_vela[coord] = ultima_vela.get(coord, 100)
        x = ultima_vela.get("x", 100)
        y = ultima_vela.get("y", 100)
        w = ultima_vela.get("w", 50)
        h = ultima_vela.get("h", 100)
        tiempo_restante = temporizador.get_tiempo_formateado()
        text_x = x + w // 2
        text_y = y + h // 2
        (text_width, text_height), baseline = cv2.getTextSize(tiempo_restante, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        seg_restantes = temporizador.get_tiempo_restante()
        if seg_restantes > 30:
            color = (0, 255, 0)
        elif seg_restantes > 10:
            color = (0, 255, 255)
        else:
            color = (0, 0, 255)
        padding = 2
        fondo_x1 = text_x - text_width // 2 - padding
        fondo_y1 = text_y - text_height // 2 - padding
        fondo_x2 = text_x + text_width // 2 + padding
        fondo_y2 = text_y + text_height // 2 + padding
        h_frame, w_frame = frame.shape[:2]
        fondo_x1 = max(0, min(fondo_x1, w_frame - 1))
        fondo_y1 = max(0, min(fondo_y1, h_frame - 1))
        fondo_x2 = max(0, min(fondo_x2, w_frame - 1))
        fondo_y2 = max(0, min(fondo_y2, h_frame - 1))
        if fondo_x1 < fondo_x2 and fondo_y1 < fondo_y2:
            cv2.rectangle(frame, (fondo_x1, fondo_y1), (fondo_x2, fondo_y2), (0, 0, 0), -1)
            cv2.rectangle(frame, (fondo_x1, fondo_y1), (fondo_x2, fondo_y2), color, 1)
            text_pos_x = max(0, min(text_x - text_width // 2, w_frame - text_width))
            text_pos_y = max(0, min(text_y + text_height // 2, h_frame - 5))
            cv2.putText(frame, tiempo_restante, (text_pos_x, text_pos_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
        return frame

    def dibujar_interfaz_completa(self, frame, señales, soportes, resistencias, temporizador, decision_conjunta, 
                                  trading_active, cooldown, inst_analysis=None):
        frame_con_interfaz = frame.copy()
        h, w = frame_con_interfaz.shape[:2]
        hora_sistema = datetime.now().strftime('%H:%M:%S')
        cv2.putText(frame_con_interfaz, f"Sistema: {hora_sistema}", (w - 200, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cierre_text = f"Cierre: {temporizador.get_proximo_cierre_str()}"
        cv2.putText(frame_con_interfaz, cierre_text, (w - 200, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        progreso = temporizador.get_tiempo_restante() / temporizador.tiempo_vela
        barra_width = 100
        barra_height = 8
        barra_x = w - barra_width - 10
        barra_y = 45
        seg_restantes = temporizador.get_tiempo_restante()
        if seg_restantes > 30:
            bar_color = (0, 255, 0)
        elif seg_restantes > 10:
            bar_color = (0, 255, 255)
        else:
            bar_color = (0, 0, 255)
        cv2.rectangle(frame_con_interfaz, (barra_x, barra_y), (barra_x + barra_width, barra_y + barra_height), (50, 50, 50), -1)
        progreso_width = int(barra_width * progreso)
        cv2.rectangle(frame_con_interfaz, (barra_x, barra_y), (barra_x + progreso_width, barra_y + barra_height), bar_color, -1)
        cv2.rectangle(frame_con_interfaz, (barra_x, barra_y), (barra_x + barra_width, barra_y + barra_height), (200, 200, 200), 1)
        for soporte in soportes:
            if 0 <= soporte <= h:
                cv2.line(frame_con_interfaz, (0, int(soporte)), (w, int(soporte)), (0, 255, 255), 1)
                cv2.putText(frame_con_interfaz, f"S: {int(soporte)}", (10, int(soporte)-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        for resistencia in resistencias:
            if 0 <= resistencia <= h:
                cv2.line(frame_con_interfaz, (0, int(resistencia)), (w, int(resistencia)), (0, 0, 255), 1)
                cv2.putText(frame_con_interfaz, f"R: {int(resistencia)}", (10, int(resistencia)-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
        estado_color = (0, 255, 0) if trading_active else (0, 0, 255)
        estado_text = "TRADING: ON" if trading_active else "TRADING: OFF"
        cv2.putText(frame_con_interfaz, estado_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, estado_color, 2)
        if cooldown > 0:
            cv2.putText(frame_con_interfaz, f"Cooldown: {cooldown}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 100, 0), 1)
        if decision_conjunta:
            accion_text = f"Decisión: {decision_conjunta['action']}"
            color_accion = (0, 255, 0) if decision_conjunta['action'] == 'COMPRA' else (0, 0, 255) if decision_conjunta['action'] == 'VENTA' else (255, 255, 255)
            cv2.putText(frame_con_interfaz, accion_text, (w - 200, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_accion, 2)
            conf_text = f"Confianza: {decision_conjunta.get('confidence', 0)*100:.0f}%"
            cv2.putText(frame_con_interfaz, conf_text, (w - 200, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            score_text = f"Score: {decision_conjunta.get('buy_score', 0):.1f}/{decision_conjunta.get('sell_score', 0):.1f}"
            cv2.putText(frame_con_interfaz, score_text, (w - 200, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 255), 1)
        if inst_analysis and 'market_index' in inst_analysis:
            mi = inst_analysis['market_index']
            inst_text = f"FX: {mi.get('buy_signals', 0)}🟢 {mi.get('sell_signals', 0)}🔴 {mi.get('direction', '')}"
            cv2.putText(frame_con_interfaz, inst_text, (10, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)

        # ----------------------------------------------------------------
        # 🧠 Panel del Transformer profundo (señal, confianza, estado)
        # ----------------------------------------------------------------
        trf = decision_conjunta.get("transformer") if decision_conjunta else None
        if trf:
            trf_y = h - 100
            status = trf.get("status", "SIN_ENTRENAR")
            trf_action = trf.get("action", "ESPERAR")
            trf_conf = trf.get("confidence", 0.0)
            if status == "CALENTANDO" or status == "SIN_ENTRENAR":
                trf_color = (0, 165, 255)
                status_label = "CALENTANDO" if status == "CALENTANDO" else "SIN ENTRENAR"
                trf_text = f"🧠 Transformer: {status_label}"
            else:
                trf_color = (0, 255, 0) if trf_action == "COMPRA" else (0, 0, 255) if trf_action == "VENTA" else (255, 255, 0)
                trf_text = f"🧠 Transformer: {trf_action} ({trf_conf*100:.0f}%)"
            cv2.putText(frame_con_interfaz, trf_text, (10, trf_y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, trf_color, 1)
            prob_text = f"   P(sube)={trf.get('prob_up', 0.5)*100:.0f}%  P(baja)={trf.get('prob_down', 0.5)*100:.0f}%  pasos={trf.get('trained_steps', 0)}"
            cv2.putText(frame_con_interfaz, prob_text, (10, trf_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

        y_text = 100
        max_señales = 5
        if señales:
            cv2.putText(frame_con_interfaz, f"Señales: {len(señales)}", (10, y_text - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 1)
        for i, señal in enumerate(señales[:max_señales]):
            color = (0, 255, 0) if señal.get("accion") == "COMPRA" else (0, 0, 255) if señal.get("accion") == "VENTA" else (255, 255, 0)
            texto = señal.get("texto", "Señal")
            if len(texto) > 25:
                texto = texto[:22] + "..."
            cv2.putText(frame_con_interfaz, texto, (10, y_text + i*25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        if decision_conjunta and 'methodologies_used' in decision_conjunta:
            metodologias = decision_conjunta['methodologies_used']
            if metodologias:
                cv2.putText(frame_con_interfaz, f"Metodologías: {len(metodologias)}", (w - 200, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 255), 1)
        divisa_activa = getattr(ConfigGlobal, "DIVISA_ACTIVA", None) or "MULTI"
        tf_label = getattr(ConfigGlobal, "TIMEFRAME_LABEL", "1m") or "1m"
        nombre_div = next((d["name"] for d in ConfigGlobal.DIVISAS if d["symbol"] == divisa_activa), divisa_activa)
        version_text = f"[{tf_label}]  {divisa_activa}  {nombre_div}"
        cv2.putText(frame_con_interfaz, version_text, (w // 2 - 150, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        controles_text = "Controles: a=Activar d=Desactivar t=Transformer q=Salir"
        cv2.putText(frame_con_interfaz, controles_text, (w // 2 - 150, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        return frame_con_interfaz

    def analisis_completo(self, frame, temporizador):
        inicio = time.time()
        try:
            velas, frame_con_contornos = self.detectar_velas_avanzado(frame)
            if not velas or len(velas) < 5:
                return {"timestamp": datetime.now(), "velas_detectadas": 0, "señales": [], "soportes": [], "resistencias": [], "tiempo_analisis": time.time() - inicio, "frame_con_contornos": frame_con_contornos}
            soportes, resistencias = self.calcular_soporte_resistencia(velas)
            señales = []
            try:
                señales.extend(self.analizar_bos(velas))
            except Exception as e:
                print(f"⚠️ Error en análisis BOS: {e}")
            if velas:
                try:
                    pinbar = self.detectar_pinbar_avanzado(velas[-1])
                    if pinbar:
                        señales.append(pinbar)
                except Exception as e:
                    print(f"⚠️ Error en detección PinBar: {e}")
            try:
                señales.extend(self.detectar_falso_rompimiento(velas, soportes, resistencias))
            except Exception as e:
                print(f"⚠️ Error en detección falsos rompimientos: {e}")
            try:
                señales.extend(self.analizar_smart_money(velas))
            except Exception as e:
                print(f"⚠️ Error en análisis Smart Money: {e}")
            señales_filtradas = self._filtrar_señales(señales)
            try:
                frame_con_temporizador = self.dibujar_temporizador_en_vela(frame_con_contornos, velas, temporizador)
            except Exception as e:
                frame_con_temporizador = frame_con_contornos
            return {"timestamp": datetime.now(), "velas_detectadas": len(velas), "señales": señales_filtradas, "soportes": soportes, "resistencias": resistencias, "ultima_vela": velas[-1] if velas else None, "metodologias_usadas": ["BOS", "PinBar", "FalsosRomp", "S/R", "SmartMoney"], "tiempo_analisis": time.time() - inicio, "frame_con_contornos": frame_con_temporizador}
        except Exception as e:
            print(f"❌ Error crítico en análisis completo: {e}")
            return {"timestamp": datetime.now(), "velas_detectadas": 0, "señales": [], "soportes": [], "resistencias": [], "tiempo_analisis": time.time() - inicio, "frame_con_contornos": frame}

    def _filtrar_señales(self, señales):
        if not señales:
            return []
        señales_por_tipo = {}
        for señal in señales:
            try:
                tipo = señal.get("accion", "NEUTRAL")
                if tipo not in señales_por_tipo:
                    señales_por_tipo[tipo] = []
                señales_por_tipo[tipo].append(señal)
            except:
                continue
        mejores_señales = []
        for tipo, lista_señales in señales_por_tipo.items():
            if tipo != "NEUTRAL" and lista_señales:
                try:
                    mejor = max(lista_señales, key=lambda x: x.get("fuerza", 0))
                    mejores_señales.append(mejor)
                except:
                    continue
        return sorted(mejores_señales, key=lambda x: x.get("fuerza", 0), reverse=True)

# =============================================================================
# 🔬 MÓDULOS ESPECIALIZADOS (ORIGINALES)
# =============================================================================

class QuantumProcessor:
    def __init__(self, num_qubits=4):
        self.num_qubits = num_qubits
        self.qubits = self._initialize_qubits()

    def _initialize_qubits(self):
        qubits = []
        for i in range(self.num_qubits):
            angle = np.random.random() * 2 * np.pi
            qubits.append({"alpha": np.cos(angle), "beta": np.sin(angle), "entanglement": 0.0})
        return qubits

    def analyze(self, prices):
        if not prices or len(prices) < 10:
            return {"signal_strength": 0.5, "quantum_state": "NEUTRAL"}
        try:
            prices_array = np.array(prices, dtype=float)
            returns = np.diff(np.log(prices_array + 1e-8))
            volatility = np.std(returns) if len(returns) > 0 else 0.01
            for i, qubit in enumerate(self.qubits):
                rotation = volatility * np.pi * (i + 1) / self.num_qubits
                new_alpha = qubit["alpha"] * np.cos(rotation) - qubit["beta"] * np.sin(rotation)
                new_beta = qubit["alpha"] * np.sin(rotation) + qubit["beta"] * np.cos(rotation)
                norm = np.sqrt(new_alpha**2 + new_beta**2)
                if norm > 0:
                    self.qubits[i]["alpha"] = new_alpha / norm
                    self.qubits[i]["beta"] = new_beta / norm
                self.qubits[i]["entanglement"] = abs(self.qubits[i]["alpha"]**2 - 0.5)
            avg_entanglement = np.mean([q["entanglement"] for q in self.qubits])
            trend = 1 if np.mean(returns) > 0 else -1 if len(returns) > 0 else 0
            signal_strength = 0.5 + trend * avg_entanglement * 0.5
            quantum_state = "BULLISH" if signal_strength > 0.6 else "BEARISH" if signal_strength < 0.4 else "NEUTRAL"
            return {"signal_strength": float(np.clip(signal_strength, 0, 1)), "quantum_state": quantum_state, "entanglement": float(avg_entanglement), "volatility_used": float(volatility)}
        except:
            return {"signal_strength": 0.5, "quantum_state": "NEUTRAL"}

class RegressionAnalyzer:
    def __init__(self):
        self.cache = {}

    def analyze(self, prices):
        if not prices or len(prices) < 10:
            return {"trend": "NEUTRAL", "trend_strength": 0.5, "r_squared": 0}
        try:
            key = hash(tuple(prices[-50:])) if len(prices) >= 50 else hash(tuple(prices))
            if key in self.cache:
                return self.cache[key]
            x = np.arange(len(prices))
            y = np.array(prices, dtype=float)
            A = np.vstack([x, np.ones(len(x))]).T
            m, c = np.linalg.lstsq(A, y, rcond=None)[0]
            y_pred = m * x + c
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / (ss_tot + 1e-8))
            price_range = np.ptp(y) if len(y) > 0 else 1
            normalized_slope = abs(m) * len(prices) / (price_range + 1e-8)
            trend_strength = min(1.0, normalized_slope * r_squared)
            if m > 0.0001 and r_squared > 0.3:
                trend = "ALCISTA"
            elif m < -0.0001 and r_squared > 0.3:
                trend = "BAJISTA"
            else:
                trend = "NEUTRAL"
            result = {"trend": trend, "trend_strength": float(trend_strength), "r_squared": float(r_squared), "slope": float(m), "intercept": float(c), "prediction": float(y_pred[-1] if len(y_pred) > 0 else prices[-1])}
            self.cache[key] = result
            return result
        except:
            return {"trend": "NEUTRAL", "trend_strength": 0.5, "r_squared": 0}

class YieldAnomalyAnalyzer:
    def __init__(self):
        self.anomaly_threshold = 2.5

    def detect_anomalies(self, prices):
        if not prices or len(prices) < 20:
            return {"anomaly_count": 0, "risk_score": 0.5, "anomaly_type": "INSUFFICIENT_DATA"}
        try:
            returns = np.diff(np.log(np.array(prices, dtype=float) + 1e-8))
            mean_return = np.mean(returns)
            std_return = np.std(returns) + 1e-8
            if len(returns) > 2 and SCIPY_DISPONIBLE:
                try:
                    skewness = skew(returns)
                except:
                    skewness = 0
            else:
                skewness = 0
            if len(returns) > 3 and SCIPY_DISPONIBLE:
                try:
                    kurt_val = kurtosis(returns)
                except:
                    kurt_val = 3
            else:
                kurt_val = 3
            z_scores = np.abs((returns - mean_return) / std_return)
            anomalies = z_scores > self.anomaly_threshold
            anomaly_count = np.sum(anomalies)
            anomaly_ratio = anomaly_count / len(returns)
            volatility_risk = min(1.0, std_return * 10)
            anomaly_risk = min(1.0, anomaly_ratio * 5)
            tail_risk = min(1.0, max(0, (abs(kurt_val) - 3) / 10))
            risk_score = (volatility_risk * 0.4 + anomaly_risk * 0.4 + tail_risk * 0.2)
            if anomaly_ratio > 0.15:
                anomaly_type = "HIGH_FREQUENCY_ANOMALIES"
            elif abs(skewness) > 1:
                anomaly_type = "SKEWED_DISTRIBUTION"
            elif kurt_val > 5:
                anomaly_type = "FAT_TAILS"
            else:
                anomaly_type = "NORMAL"
            return {"anomaly_count": int(anomaly_count), "anomaly_ratio": float(anomaly_ratio), "risk_score": float(risk_score), "anomaly_type": anomaly_type, "volatility": float(std_return), "skewness": float(skewness), "kurtosis": float(kurt_val)}
        except:
            return {"anomaly_count": 0, "risk_score": 0.5, "anomaly_type": "ERROR"}

class StatisticalArbitrageAnalyzer:
    def __init__(self):
        self.cointegration_cache = {}

    def find_opportunities(self, forex_prices):
        if not forex_prices or len(forex_prices) < 3:
            return []
        try:
            symbols = list(forex_prices.keys())
            opportunities = []
            valid_pairs = []
            for i in range(len(symbols)):
                for j in range(i + 1, len(symbols)):
                    sym1, sym2 = symbols[i], symbols[j]
                    price1 = forex_prices.get(sym1)
                    price2 = forex_prices.get(sym2)
                    if price1 is not None and price2 is not None and price2 != 0:
                        valid_pairs.append((sym1, sym2, price1, price2))
            for sym1, sym2, price1, price2 in valid_pairs:
                ratio = price1 / price2
                closes1 = UnifiedForexDataProvider.get_real_closes(sym1, candles=20)
                closes2 = UnifiedForexDataProvider.get_real_closes(sym2, candles=20)
                if closes1 and closes2 and len(closes1) == len(closes2) and len(closes1) >= 3:
                    ratios_history = [c1 / c2 for c1, c2 in zip(closes1, closes2) if c2 != 0]
                else:
                    ratios_history = []
                if len(ratios_history) < 3:
                    continue  # sin histórico real suficiente, se descarta el par (no se inventan datos)
                ratio_mean = np.mean(ratios_history)
                ratio_std = np.std(ratios_history)
                if ratio_std > 0:
                    z_score = (ratio - ratio_mean) / ratio_std
                    if abs(z_score) > 2.0:
                        opportunity = {"pair": f"{sym1}/{sym2}", "current_ratio": float(ratio), "mean_ratio": float(ratio_mean), "z_score": float(z_score), "signal": "COMPRA_1_VENTA_2" if z_score < -2 else "VENTA_1_COMPRA_2", "spread": float(abs(z_score)), "confidence": float(min(0.9, abs(z_score) / 4))}
                        opportunities.append(opportunity)
            return sorted(opportunities, key=lambda x: abs(x["z_score"]), reverse=True)[:3]
        except:
            return []

# =============================================================================
# 🌐 MÓDULO DE ANÁLISIS INSTITUCIONAL MODIFICADO PARA USAR PROVEEDOR UNIFICADO
# =============================================================================

class InstitutionalAnalyzer:
    def __init__(self):
        self.divisas_data = {}
        self.quantum_processor = QuantumProcessor()
        self.regression_analyzer = RegressionAnalyzer()
        self.yield_analyzer = YieldAnomalyAnalyzer()
        self.arbitrage_analyzer = StatisticalArbitrageAnalyzer()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=ConfigGlobal.PARALLEL_WORKERS)
        print("✅ Institutional Analyzer (Divisas Forex - múltiples fuentes gratuitas)")
        self._initialize_data()

    def _initialize_data(self):
        print("\n📊 Cargando datos reales de divisas forex (múltiples fuentes)...")
        divisa_activa = getattr(ConfigGlobal, "DIVISA_ACTIVA", None)
        if divisa_activa:
            divisas_a_cargar = [d for d in ConfigGlobal.DIVISAS if d["symbol"] == divisa_activa]
            if not divisas_a_cargar:
                print(f"❌ Símbolo '{divisa_activa}' no encontrado.")
                sys.exit(1)
            else:
                print(f"   🎯 Filtro activo: solo se opera {divisa_activa}")
        else:
            divisas_a_cargar = ConfigGlobal.DIVISAS

        for divisa in divisas_a_cargar:
            symbol = divisa["symbol"]
            # Obtener precio real usando el proveedor unificado
            current_price = UnifiedForexDataProvider.get_current_price(symbol)
            reintentos = 0
            while current_price is None and reintentos < 3:
                time.sleep(1)
                current_price = UnifiedForexDataProvider.get_current_price(symbol)
                reintentos += 1
            if current_price is None:
                print(f"   ❌ {symbol}: No se pudo obtener precio real después de reintentos. Saliendo.")
                sys.exit(1)

            # Histórico REAL: cierres reales recientes (Yahoo Finance, vela 1m)
            prices_reales = UnifiedForexDataProvider.get_real_closes(symbol, candles=ConfigGlobal.HISTORY_POINTS)
            if prices_reales and len(prices_reales) >= 2:
                prices = prices_reales[-ConfigGlobal.HISTORY_POINTS:]
                if prices[-1] != current_price:
                    prices.append(current_price)
            else:
                # Sin histórico real disponible aún: se inicia solo con el precio real actual
                prices = [current_price]

            # Volumen REAL de la última vela (si está disponible la fuente Yahoo)
            ultima_vela = UnifiedForexDataProvider.get_real_last_candle(symbol)
            volumen_real = ultima_vela["volume"] if ultima_vela and ultima_vela.get("volume") else 0.0

            self.divisas_data[symbol] = {
                "prices": prices,
                "current_price": current_price,
                "volume": volumen_real,
                "market_cap": 0,
                "volatility": divisa["volatility"],
                "weight": divisa["weight"],
                "last_update": datetime.now(),
                "data_source": "MULTI_FUENTE_LIVE"
            }
            print(f"   ✅ {symbol}: {current_price:.6f} (precio real)")
        self.crypto_data = self.divisas_data
        print(f"   📊 Total cargadas: {len(divisas_a_cargar)} divisas (datos reales)")

    def quantum_analysis(self, prices):
        return self.quantum_processor.analyze(prices)

    def regression_analysis(self, prices):
        return self.regression_analyzer.analyze(prices)

    def yield_anomaly_analysis(self, prices):
        return self.yield_analyzer.detect_anomalies(prices)

    def statistical_arbitrage(self, forex_prices):
        return self.arbitrage_analyzer.find_opportunities(forex_prices)

    def analyze_single_crypto(self, symbol):
        if symbol not in self.divisas_data:
            return None
        data = self.divisas_data[symbol]
        # Actualizar precio actual en tiempo real
        real_price = UnifiedForexDataProvider.get_current_price(symbol)
        if real_price is not None:
            data["current_price"] = real_price
            # Actualizar histórico
            prices = data.get("prices", [])
            prices.append(real_price)
            if len(prices) > ConfigGlobal.HISTORY_POINTS:
                prices.pop(0)
            data["prices"] = prices
            data["last_update"] = datetime.now()
        prices = data.get("prices", [])
        if len(prices) < 20:
            return None
        try:
            prices = [float(p) for p in prices]
        except:
            return None

        quantum_result = self.quantum_analysis(prices)
        regression_result = self.regression_analysis(prices)
        yield_result = self.yield_anomaly_analysis(prices)

        signal_score = self._calculate_composite_signal(quantum_result, regression_result, yield_result)
        action = "NEUTRAL"
        if signal_score >= 0.6:
            action = "COMPRA"
        elif signal_score <= 0.4:
            action = "VENTA"

        return {
            "symbol": symbol,
            "current_price": data["current_price"],
            "signal_score": signal_score,
            "action": action,
            "quantum": quantum_result,
            "regression": regression_result,
            "yield_anomaly": yield_result,
            "confidence": min(0.95, abs(signal_score - 0.5) * 2),
            "timestamp": datetime.now()
        }

    def _calculate_composite_signal(self, quantum, regression, yield_anomaly):
        quantum_weight = 0.4
        regression_weight = 0.35
        yield_weight = 0.25
        try:
            quantum_score = float(quantum.get("signal_strength", 0.5))
        except:
            quantum_score = 0.5
        try:
            regression_score = float(regression.get("trend_strength", 0.5))
        except:
            regression_score = 0.5
        try:
            yield_score = 1.0 - float(yield_anomaly.get("risk_score", 0.5))
        except:
            yield_score = 0.5
        composite = quantum_score * quantum_weight + regression_score * regression_weight + yield_score * yield_weight
        return float(np.clip(composite, 0, 1))

    def analyze_market(self):
        inicio = time.time()
        divisa_activa = getattr(ConfigGlobal, "DIVISA_ACTIVA", None)
        if divisa_activa:
            divisas_a_analizar = [d for d in ConfigGlobal.DIVISAS if d["symbol"] == divisa_activa]
            if not divisas_a_analizar:
                divisas_a_analizar = ConfigGlobal.DIVISAS
        else:
            divisas_a_analizar = ConfigGlobal.DIVISAS

        analyses = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=ConfigGlobal.PARALLEL_WORKERS) as executor:
            futures = [executor.submit(self.analyze_single_crypto, d["symbol"]) for d in divisas_a_analizar]
            for future in concurrent.futures.as_completed(futures):
                try:
                    analysis = future.result(timeout=10)
                    if analysis:
                        analyses.append(analysis)
                except Exception as e:
                    print(f"⚠️ Error en análisis de divisa: {e}")

        market_index = self._calculate_market_index(analyses)
        arbitrage_ops = []
        try:
            if len(analyses) > 1:
                price_dict = {a["symbol"]: a["current_price"] for a in analyses}
                arbitrage_ops = self.statistical_arbitrage(price_dict)
        except:
            pass

        return {
            "timestamp": datetime.now(),
            "individual_analyses": analyses,
            "market_index": market_index,
            "arbitrage_opportunities": arbitrage_ops,
            "total_cryptos": len(analyses),
            "divisa_activa": divisa_activa,
            "analysis_time": time.time() - inicio
        }

    def _calculate_market_index(self, analyses):
        if not analyses:
            return {"direction": "NEUTRAL", "buy_signals": 0, "sell_signals": 0, "avg_confidence": 0}
        buy_signals = sum(1 for a in analyses if a["action"] == "COMPRA")
        sell_signals = sum(1 for a in analyses if a["action"] == "VENTA")
        confidences = [a["confidence"] for a in analyses if a["confidence"] > 0]
        avg_conf = np.mean(confidences) if confidences else 0
        if buy_signals > sell_signals + 1:
            direction = "ALCISTA FUERTE 📈" if buy_signals - sell_signals >= 3 else "ALCISTA 📈"
        elif sell_signals > buy_signals + 1:
            direction = "BAJISTA FUERTE 📉" if sell_signals - buy_signals >= 3 else "BAJISTA 📉"
        else:
            direction = "LATERAL ↔️"
        return {
            "direction": direction,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "avg_confidence": avg_conf,
            "strength": abs(buy_signals - sell_signals) / max(1, buy_signals + sell_signals)
        }

# =============================================================================
# 🤖 SISTEMA DE DECISIÓN CONJUNTA AVANZADO (ORIGINAL)
# =============================================================================

class AdvancedDecisionSystem:
    def __init__(self):
        self.pa_analyzer = PriceActionAnalyzer()
        self.inst_analyzer = InstitutionalAnalyzer()
        self.tech_analyzer = TechnicalIndicatorAnalyzer()
        self.transformer_engine = TransformerSignalEngine(self.tech_analyzer)
        self.decision_history = deque(maxlen=50)
        self.performance_metrics = {"total_decisions": 0, "avg_confidence": 0.0}
        self.last_transformer_signal = {
            "action": "ESPERAR", "confidence": 0.0, "prob_up": 0.5, "prob_down": 0.5,
            "status": "SIN_ENTRENAR", "trained_steps": 0
        }
        print("✅ Advanced Decision System inicializado (con indicadores técnicos + Transformer)")

    def initialize_transformer(self):
        """Entrena el Transformer una sola vez al arrancar, con datos reales de la divisa activa."""
        symbol = ConfigGlobal.DIVISA_ACTIVA
        if not symbol:
            return
        try:
            self.transformer_engine.initial_train(symbol)
        except Exception as e:
            print(f"⚠️ Error en entrenamiento inicial del Transformer: {e}")

    def _technical_signals(self, inst_analysis):
        """Genera señales MACD/Stoch/RSI/Bollinger a partir de precios REALES
        del par activo (histórico ya alimentado por UnifiedForexDataProvider)."""
        señales = []
        try:
            symbol = ConfigGlobal.DIVISA_ACTIVA
            if not symbol or not isinstance(inst_analysis, dict):
                return señales
            data = self.inst_analyzer.divisas_data.get(symbol, {})
            prices = data.get("prices", [])
            if len(prices) < max(ConfigGlobal.MACD_SLOW, ConfigGlobal.STOCH_K, ConfigGlobal.BB_PERIOD) + 2:
                return señales  # histórico real insuficiente todavía
            macd = self.tech_analyzer.compute_macd(prices)
            stoch = self.tech_analyzer.compute_stochastic(prices)
            rsi = self.tech_analyzer.compute_rsi(prices)
            bb = self.tech_analyzer.compute_bollinger(prices)
            if macd.get("trend") == "ALCISTA_CRUCE":
                señales.append({"accion": "COMPRA", "fuerza": 1.5, "texto": "📈 MACD cruce alcista", "metodologia": "MACD"})
            elif macd.get("trend") == "BAJISTA_CRUCE":
                señales.append({"accion": "VENTA", "fuerza": 1.5, "texto": "📉 MACD cruce bajista", "metodologia": "MACD"})
            if stoch.get("cruce") == "ALCISTA" and stoch.get("position") != "SOBRECOMPRA":
                señales.append({"accion": "COMPRA", "fuerza": 1.0, "texto": "📈 Stoch cruce alcista", "metodologia": "Stochastic"})
            elif stoch.get("cruce") == "BAJISTA" and stoch.get("position") != "SOBREVENTA":
                señales.append({"accion": "VENTA", "fuerza": 1.0, "texto": "📉 Stoch cruce bajista", "metodologia": "Stochastic"})
            if rsi.get("position") == "SOBREVENTA":
                señales.append({"accion": "COMPRA", "fuerza": 0.8, "texto": f"📈 RSI sobreventa ({rsi['rsi']:.1f})", "metodologia": "RSI"})
            elif rsi.get("position") == "SOBRECOMPRA":
                señales.append({"accion": "VENTA", "fuerza": 0.8, "texto": f"📉 RSI sobrecompra ({rsi['rsi']:.1f})", "metodologia": "RSI"})
            if bb.get("position") == "SOBRE_BANDA_INFERIOR":
                señales.append({"accion": "COMPRA", "fuerza": 0.7, "texto": "📈 Precio bajo banda Bollinger", "metodologia": "Bollinger"})
            elif bb.get("position") == "SOBRE_BANDA_SUPERIOR":
                señales.append({"accion": "VENTA", "fuerza": 0.7, "texto": "📉 Precio sobre banda Bollinger", "metodologia": "Bollinger"})
        except Exception as e:
            print(f"⚠️ Error en señales técnicas: {e}")
        return señales

    def _transformer_signal(self, inst_analysis):
        """Obtiene la señal del Transformer profundo a partir del histórico real
        de precios de la divisa activa, y dispara reentrenamiento periódico."""
        señales = []
        try:
            symbol = ConfigGlobal.DIVISA_ACTIVA
            if not symbol or not isinstance(inst_analysis, dict):
                return señales
            data = self.inst_analyzer.divisas_data.get(symbol, {})
            prices = data.get("prices", [])
            result = self.transformer_engine.get_signal(prices)
            self.last_transformer_signal = result
            self.transformer_engine.maybe_retrain_async(symbol)
            if result.get("action") in ("COMPRA", "VENTA") and result.get("status") == "ENTRENADO":
                conf = result.get("confidence", 0.0)
                if conf >= ConfigGlobal.TRANSFORMER_CONF_MIN:
                    fuerza = ConfigGlobal.TRANSFORMER_WEIGHT * conf
                    emoji = "📈" if result["action"] == "COMPRA" else "📉"
                    señales.append({
                        "accion": result["action"],
                        "fuerza": fuerza,
                        "texto": f"{emoji} Transformer ({conf:.0%})",
                        "metodologia": "Transformer"
                    })
        except Exception as e:
            print(f"⚠️ Error en señal del Transformer: {e}")
        return señales

    def evaluate_hybrid_signal(self, pa_analysis, inst_analysis):
        inicio = time.time()
        try:
            pa_signals = pa_analysis.get("señales", []) if isinstance(pa_analysis, dict) else []
            inst_signals = []
            if isinstance(inst_analysis, dict) and "market_index" in inst_analysis:
                mi = inst_analysis["market_index"]
                direction = mi.get("direction", "")
                if "ALCISTA" in direction:
                    strength = mi.get("strength", 0.5)
                    inst_signals.append({"accion": "COMPRA", "fuerza": strength * 2.0, "texto": f"📈 INST: {direction}"})
                elif "BAJISTA" in direction:
                    strength = mi.get("strength", 0.5)
                    inst_signals.append({"accion": "VENTA", "fuerza": strength * 2.0, "texto": f"📉 INST: {direction}"})
            tech_signals = self._technical_signals(inst_analysis)
            transformer_signals = self._transformer_signal(inst_analysis)
            all_signals = list(pa_signals) + inst_signals + tech_signals + transformer_signals
            if not all_signals:
                return self._neutral_decision()
            buy_score = sum(s.get("fuerza", 0) for s in all_signals if s.get("accion") == "COMPRA")
            sell_score = sum(s.get("fuerza", 0) for s in all_signals if s.get("accion") == "VENTA")
            # Bias cuántico y regresión
            quantum_bias = 0.0
            regression_bias = 0.0
            if isinstance(inst_analysis, dict) and "individual_analyses" in inst_analysis:
                q_scores = []
                r_scores = []
                for a in inst_analysis["individual_analyses"]:
                    q = a.get("quantum", {}).get("signal_strength", 0.5)
                    r = a.get("regression", {}).get("trend_strength", 0.5)
                    q_scores.append(q)
                    r_scores.append(r)
                if q_scores:
                    quantum_bias = (np.mean(q_scores) - 0.5) * 2.0
                if r_scores:
                    regression_bias = (np.mean(r_scores) - 0.5) * 2.0
            total_buy = buy_score + quantum_bias + regression_bias
            total_sell = sell_score - quantum_bias - regression_bias
            threshold = 3.0
            action = "ESPERAR"
            confidence = 0.0
            if total_buy - total_sell >= threshold:
                action = "COMPRA"
                confidence = min(0.95, (total_buy - total_sell) / 10.0)
            elif total_sell - total_buy >= threshold:
                action = "VENTA"
                confidence = min(0.95, (total_sell - total_buy) / 10.0)
            methodologies = list(set(s.get("metodologia", "") for s in all_signals if s.get("metodologia")))
            decision = {
                "timestamp": datetime.now(),
                "action": action,
                "confidence": confidence,
                "buy_score": total_buy,
                "sell_score": total_sell,
                "pa_signals": len(pa_signals),
                "inst_signals": len(inst_signals),
                "methodologies_used": methodologies,
                "analysis_time": time.time() - inicio,
                "transformer": self.last_transformer_signal
            }
            self.decision_history.append(decision)
            self.performance_metrics["total_decisions"] += 1
            if action != "ESPERAR":
                self.performance_metrics["avg_confidence"] = self.performance_metrics["avg_confidence"] * 0.9 + confidence * 0.1
            return decision
        except Exception as e:
            print(f"⚠️ Error evaluando señal híbrida: {e}")
            return self._neutral_decision()

    def _neutral_decision(self):
        return {
            "timestamp": datetime.now(),
            "action": "ESPERAR",
            "confidence": 0.1,
            "buy_score": 0,
            "sell_score": 0,
            "pa_signals": 0,
            "inst_signals": 0,
            "methodologies_used": [],
            "analysis_time": 0.001,
            "transformer": self.last_transformer_signal
        }

    def get_performance_report(self):
        return {**self.performance_metrics, "decision_count": len(self.decision_history)}

# =============================================================================
# 🎮 SISTEMA DE TRADING CONJUNTO AVANZADO CON INTERFAZ VISUAL (ORIGINAL)
# =============================================================================

class AdvancedTradingSystem:
    def __init__(self):
        if ConfigGlobal.TIMEFRAME_SEGUNDOS is None:
            self._seleccionar_timeframe()
        else:
            self._aplicar_timeframe(ConfigGlobal.TIMEFRAME_SEGUNDOS)
        if ConfigGlobal.DIVISA_ACTIVA is None:
            ConfigGlobal.DIVISA_ACTIVA = self._seleccionar_divisa()
        else:
            nombre = next((d["name"] for d in ConfigGlobal.DIVISAS if d["symbol"] == ConfigGlobal.DIVISA_ACTIVA), ConfigGlobal.DIVISA_ACTIVA)
            print(f"\n🎯 Divisa activa (config): {ConfigGlobal.DIVISA_ACTIVA} — {nombre}")
        self.temporizador = AdvancedTemporizador(ConfigGlobal.TIEMPO_VELA_SEGUNDOS)
        self.decision_system = AdvancedDecisionSystem()
        # 🧠 Entrenamiento automático del Transformer con datos reales al iniciar
        self.decision_system.initialize_transformer()
        self.trading_active = False
        self.cooldown = 0
        self.ciclo_count_global = 0
        self.operation_history = deque(maxlen=100)
        self.last_operation = None
        self.last_frame_with_interface = None
        # 💰 Capital Tracker: lee el saldo real por OCR, registra ganadas/perdidas
        # y alimenta el refuerzo Q-Learning del Transformer con el resultado real.
        self.capital_tracker = CapitalTracker()
        self._capital_last_check = 0.0
        self.BUY_COORDS = ConfigGlobal.BUY_COORDS
        self.SELL_COORDS = ConfigGlobal.SELL_COORDS
        if TRADING_DISPONIBLE:
            pyautogui.PAUSE = 0.1
            pyautogui.FAILSAFE = True
        print(f"✅ Advanced Trading System inicializado  |  Timeframe: {ConfigGlobal.TIMEFRAME_LABEL}  |  Divisa: {ConfigGlobal.DIVISA_ACTIVA}")

    @staticmethod
    def _aplicar_timeframe(segundos):
        ConfigGlobal.TIMEFRAME_SEGUNDOS = segundos
        ConfigGlobal.TIEMPO_VELA_SEGUNDOS = segundos
        if segundos == 60:
            ConfigGlobal.TIMEFRAME_LABEL = "1m"
            ConfigGlobal.YF_INTERVAL = "1m"
            ConfigGlobal.HISTORY_POINTS = 60
        elif segundos == 300:
            ConfigGlobal.TIMEFRAME_LABEL = "5m"
            ConfigGlobal.YF_INTERVAL = "5m"
            ConfigGlobal.HISTORY_POINTS = 60
        else:
            ConfigGlobal.TIMEFRAME_LABEL = f"{segundos//60}m"
            ConfigGlobal.YF_INTERVAL = "1m"
            ConfigGlobal.HISTORY_POINTS = 60

    @staticmethod
    def _seleccionar_timeframe():
        opciones = {"1": (60, "1 minuto"), "2": (300, "5 minutos")}
        print("\n" + "="*60)
        print("⏱️ SELECCIÓN DE TIMEFRAME")
        print("="*60)
        for k, (seg, desc) in opciones.items():
            print(f"   {k}. {desc}")
        while True:
            raw = input("   Elige (1/2): ").strip()
            if raw in opciones:
                seg, desc = opciones[raw]
                AdvancedTradingSystem._aplicar_timeframe(seg)
                print(f"\n✅ Timeframe: {ConfigGlobal.TIMEFRAME_LABEL} — {desc}")
                return
            print("   ⚠️ Opción inválida")

    def _seleccionar_divisa(self):
        print("\n" + "="*60)
        print("💱 SELECCIÓN DE DIVISA A OPERAR")
        print("="*60)
        for i, d in enumerate(ConfigGlobal.DIVISAS, 1):
            print(f"   {i:>2}. {d['symbol']:12s}  {d['name']}")
        while True:
            try:
                raw = input("   Número (1-8): ").strip()
                idx = int(raw) - 1
                if 0 <= idx < len(ConfigGlobal.DIVISAS):
                    elegida = ConfigGlobal.DIVISAS[idx]
                    print(f"\n✅ Divisa seleccionada: {elegida['symbol']} — {elegida['name']}")
                    return elegida["symbol"]
                else:
                    print(f"   ⚠️ Número entre 1 y {len(ConfigGlobal.DIVISAS)}")
            except ValueError:
                print("   ⚠️ Entrada inválida")

    def activate_trading(self):
        if TRADING_DISPONIBLE:
            self.trading_active = True
            print("🟢 TRADING AVANZADO ACTIVADO")
        else:
            print("❌ PyAutoGUI no disponible")

    def deactivate_trading(self):
        self.trading_active = False
        print("🔴 TRADING AVANZADO DESACTIVADO")

    def execute_cycle(self):
        inicio_ciclo = time.time()
        try:
            frame = self.decision_system.pa_analyzer.capturar_pantalla()
        except:
            frame = np.zeros((ConfigGlobal.MONITOR["height"], ConfigGlobal.MONITOR["width"], 3), dtype=np.uint8)
        try:
            pa_analysis = self.decision_system.pa_analyzer.analisis_completo(frame, self.temporizador)
        except:
            pa_analysis = {"timestamp": datetime.now(), "velas_detectadas": 0, "señales": [], "soportes": [], "resistencias": [], "frame_con_contornos": frame}
        try:
            inst_analysis = self.decision_system.inst_analyzer.analyze_market()
        except:
            inst_analysis = {"timestamp": datetime.now(), "individual_analyses": [], "market_index": {"direction": "ERROR", "buy_signals": 0, "sell_signals": 0}, "total_cryptos": 0}
        try:
            decision = self.decision_system.evaluate_hybrid_signal(pa_analysis, inst_analysis)
        except:
            decision = {"timestamp": datetime.now(), "action": "ESPERAR", "confidence": 0.0, "buy_score": 0, "sell_score": 0}
        try:
            cierre_vela = self.temporizador.actualizar()
        except:
            cierre_vela = False
        try:
            frame_with_interface = self.decision_system.pa_analyzer.dibujar_interfaz_completa(
                pa_analysis.get("frame_con_contornos", frame), pa_analysis.get("señales", []),
                pa_analysis.get("soportes", []), pa_analysis.get("resistencias", []),
                self.temporizador, decision, self.trading_active, self.cooldown, inst_analysis)
            self.last_frame_with_interface = frame_with_interface
        except:
            frame_with_interface = frame
        try:
            if self.trading_active and cierre_vela and decision.get("action") in ["COMPRA", "VENTA"] and decision.get("confidence", 0) > 0.5 and self.cooldown == 0:
                if self._execute_trade(decision):
                    # Guardamos la secuencia de features que generó esta decisión: la
                    # necesitaremos para reforzar al Transformer cuando sepamos, por el
                    # capital real, si la operación fue GANADA o PERDIDA.
                    feats_seq = self.decision_system.transformer_engine.get_last_feats_seq()
                    self.last_operation = {
                        **decision, "executed": True, "execution_time": datetime.now(),
                        "feats_seq": feats_seq, "_capital_evaluada": False
                    }
                    self.operation_history.append(self.last_operation)
                    self.cooldown = ConfigGlobal.COOLDOWN_CICLOS
        except:
            pass
        # 💰 Lectura periódica del capital real + refuerzo Q-Learning con el resultado
        try:
            ahora = time.time()
            if (ConfigGlobal.CAPITAL_OCR_ENABLED and self.capital_tracker.habilitado and
                    (ahora - self._capital_last_check) >= ConfigGlobal.CAPITAL_CHECK_INTERVAL_SEGUNDOS):
                self._capital_last_check = ahora
                entrada_capital = self.capital_tracker.actualizar()
                if entrada_capital is not None:
                    self._procesar_resultado_capital(entrada_capital)
        except Exception:
            pass
        if self.cooldown > 0:
            self.cooldown -= 1
        ciclo_time = time.time() - inicio_ciclo
        return {
            "decision": decision,
            "pa_analysis": pa_analysis,
            "inst_analysis": inst_analysis,
            "cierre_vela": cierre_vela,
            "cycle_time": ciclo_time,
            "cooldown": self.cooldown,
            "trading_active": self.trading_active,
            "frame_with_interface": frame_with_interface
        }

    def _execute_trade(self, decision):
        try:
            if decision["action"] == "COMPRA":
                print(f"\n{'='*60}")
                print("🤖 EJECUTANDO COMPRA CONJUNTA AVANZADA")
                print(f"{'='*60}")
                print(f"🕐 Hora: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
                print(f"🎯 Decisión: COMPRA")
                print(f"📊 Confianza: {decision['confidence']:.1%}")
                if TRADING_DISPONIBLE:
                    pyautogui.moveTo(self.BUY_COORDS[0], self.BUY_COORDS[1], duration=0.05)
                    pyautogui.click()
                print("✅ COMPRA EJECUTADA")
                return True
            elif decision["action"] == "VENTA":
                print(f"\n{'='*60}")
                print("🤖 EJECUTANDO VENTA CONJUNTA AVANZADA")
                print(f"{'='*60}")
                print(f"🕐 Hora: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
                print(f"🎯 Decisión: VENTA")
                print(f"📊 Confianza: {decision['confidence']:.1%}")
                if TRADING_DISPONIBLE:
                    pyautogui.moveTo(self.SELL_COORDS[0], self.SELL_COORDS[1], duration=0.05)
                    pyautogui.click()
                print("✅ VENTA EJECUTADA")
                return True
        except Exception as e:
            print(f"❌ Error ejecutando {decision['action']}: {e}")
        return False

    def _procesar_resultado_capital(self, entrada):
        """
        Conecta la lectura de capital real (OCR) con la última operación
        ejecutada: si el capital subió tras operar => GANADA, si bajó => PERDIDA.
        A partir de eso deriva la etiqueta REAL de dirección de precio
        (label=1 si el precio realmente subió, 0 si bajó) y refuerza al
        Transformer con ese desenlace verdadero (Q-Learning sobre resultados
        reales, no solo sobre el siguiente cierre de vela).
        """
        resultado = entrada.get("resultado")
        if resultado not in ("GANADA", "PERDIDA"):
            return  # NEUTRA o INICIAL: no hay operación que evaluar todavía
        op = self.last_operation
        if not op or op.get("_capital_evaluada"):
            return
        feats_seq = op.get("feats_seq")
        accion = op.get("action")
        if feats_seq is None or accion not in ("COMPRA", "VENTA"):
            return

        ganada = (resultado == "GANADA")
        # Si COMPRA ganó (o VENTA perdió) el precio realmente subió -> label 1
        # Si VENTA ganó (o COMPRA perdió) el precio realmente bajó -> label 0
        label = 1 if (accion == "COMPRA") == ganada else 0
        try:
            reforzado = self.decision_system.transformer_engine.reinforce_from_outcome(
                feats_seq, label, resultado)
            op["_capital_evaluada"] = True
            op["resultado_capital"] = resultado
            emoji = "✅" if ganada else "❌"
            extra = " | 🧠 Transformer reforzado" if reforzado else ""
            print(f"{emoji} [Capital] Operación {accion} evaluada como {resultado} "
                  f"(Δ {entrada['diff_prev']:+,.2f} C$, {entrada['var_prev']:+.2f}%){extra}")
        except Exception as e:
            print(f"⚠️ [Capital] Error reforzando el Transformer con el resultado real: {e}")

    def run_continuous_with_visual(self):
        divisa_activa = ConfigGlobal.DIVISA_ACTIVA
        tf_label = ConfigGlobal.TIMEFRAME_LABEL
        nombre_divisa = next((d["name"] for d in ConfigGlobal.DIVISAS if d["symbol"] == divisa_activa), divisa_activa)
        titulo_ventana = f"SISTEMA HÍBRIDO [{tf_label}] {divisa_activa} — {nombre_divisa}"
        print("\n" + "="*80)
        print(f"🚀 SISTEMA HÍBRIDO ULTRA ROBUSTO - MÚLTIPLES FUENTES GRATUITAS")
        print(f"   💱 Operando: {divisa_activa} — {nombre_divisa}")
        print(f"   ⏱️ Timeframe: {tf_label}")
        print("="*80)
        if TRADING_DISPONIBLE:
            resp = input("\n¿Activar trading automático? (s/n): ").lower()
            if resp == 's':
                self.activate_trading()
        print(f"\n⏰ Próximo cierre: {self.temporizador.proximo_cierre.strftime('%H:%M:%S')}")
        print("🖥️ Interfaz visual activada")
        print("-" * 80)
        ciclo_count = 0
        last_display_time = time.time()
        cv2.namedWindow(titulo_ventana, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(titulo_ventana, 1200, 700)
        try:
            while True:
                ciclo_count += 1
                result = self.execute_cycle()
                if result and "frame_with_interface" in result:
                    cv2.imshow(titulo_ventana, result["frame_with_interface"])
                current_time = time.time()
                if current_time - last_display_time > 2.0 or result.get("cierre_vela", False):
                    self._display_cycle_info(result, ciclo_count)
                    last_display_time = current_time
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('a'):
                    self.activate_trading()
                elif key == ord('d'):
                    self.deactivate_trading()
                elif key == ord('s'):
                    stats = self.temporizador.get_sincronizacion_stats()
                    print(f"\n📊 Sincronización: desv. prom. {stats.get('desviacion_promedio_ms',0):.1f}ms")
                elif key == ord('p'):
                    report = self.decision_system.get_performance_report()
                    print(f"\n📈 Rendimiento: {report.get('total_decisions',0)} decisiones")
                elif key == ord('t'):
                    trf = self.decision_system.last_transformer_signal
                    eng = self.decision_system.transformer_engine
                    print(f"\n🧠 Transformer: status={trf.get('status')} | acción={trf.get('action')} | "
                          f"confianza={trf.get('confidence',0):.1%} | P(sube)={trf.get('prob_up',0.5):.1%} | "
                          f"pasos_entrenados={trf.get('trained_steps',0)} | "
                          f"ciclos_hasta_reentreno={ConfigGlobal.TRANSFORMER_RETRAIN_CICLOS - eng.cycles_since_train} | "
                          f"reentrenando={eng.training_in_progress}")
                elif key == ord('c') and self.last_frame_with_interface is not None:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    cv2.imwrite(f"screenshot_{ts}.png", self.last_frame_with_interface)
                    print(f"\n📸 Captura guardada")
                time.sleep(max(0.05, 0.1 - result.get("cycle_time", 0)))
        except KeyboardInterrupt:
            print("\n🛑 Sistema detenido")
        finally:
            cv2.destroyAllWindows()
            self._show_final_report()

    def _display_cycle_info(self, result, ciclo_count):
        try:
            decision = result.get("decision", {})
            pa = result.get("pa_analysis", {})
            inst = result.get("inst_analysis", {})
            hora = datetime.now().strftime('%H:%M:%S')
            seg_rest = self.temporizador.get_tiempo_restante()
            precio_str = ""
            divisa_activa = ConfigGlobal.DIVISA_ACTIVA
            for a in inst.get("individual_analyses", []):
                if a.get("symbol") == divisa_activa:
                    precio = a.get("current_price")
                    if precio:
                        precio_str = f"{precio:.6f}"
                        break
            color = ""
            accion = decision.get("action", "ESPERAR")
            if accion == "COMPRA":
                color = "\033[92m"
            elif accion == "VENTA":
                color = "\033[91m"
            else:
                color = "\033[93m"
            reset = "\033[0m"
            velas = pa.get("velas_detectadas", 0)
            pa_sen = len(pa.get("señales", []))
            mi = inst.get("market_index", {})
            buy = mi.get("buy_signals", 0)
            sell = mi.get("sell_signals", 0)
            conf = decision.get("confidence", 0)
            trf = decision.get("transformer", {})
            trf_action = trf.get("action", "—")
            trf_conf = trf.get("confidence", 0.0)
            trf_status = trf.get("status", "—")
            if trf_status == "ENTRENADO":
                trf_str = f"TRF:{trf_action[:3]} {trf_conf:.0%}"
            else:
                trf_str = f"TRF:{trf_status[:4]}"
            if precio_str:
                print(f"\r[{hora}] C{ciclo_count:04d} | ⏳{seg_rest:2d}s | {divisa_activa}: {precio_str} | PA:{velas:2d}v {pa_sen:1d}s | FX:{buy}🟢{sell}🔴 | {trf_str} | {color}{accion:6s} {conf:.0%}{reset} | CD:{result.get('cooldown',0)} | ⚡{result.get('cycle_time',0):.2f}s", end="")
            else:
                print(f"\r[{hora}] C{ciclo_count:04d} | ⏳{seg_rest:2d}s | PA:{velas:2d}v {pa_sen:1d}s | FX:{buy}🟢{sell}🔴 | {trf_str} | {color}{accion:6s} {conf:.0%}{reset} | CD:{result.get('cooldown',0)} | ⚡{result.get('cycle_time',0):.2f}s", end="")
            if result.get("cierre_vela"):
                print("\n🔔 VELA CERRADA")
        except:
            pass

    def _show_final_report(self):
        print("\n" + "="*80)
        print("📊 REPORTE FINAL")
        print(f"Operaciones ejecutadas: {len(self.operation_history)}")
        compras = sum(1 for op in self.operation_history if op.get("action")=="COMPRA")
        ventas = sum(1 for op in self.operation_history if op.get("action")=="VENTA")
        print(f"Compras: {compras} | Ventas: {ventas}")

        # 💰 CAPITAL: inicial, final y diferencia (registro completo vía OCR)
        print("-"*80)
        resumen = self.capital_tracker.resumen_final()
        if resumen:
            signo = '+' if resumen['diferencia'] >= 0 else ''
            print("💰 CAPITAL")
            print(f"   Capital inicial : C$ {resumen['capital_inicial']:,.2f}")
            print(f"   Capital final   : C$ {resumen['capital_final']:,.2f}")
            print(f"   Diferencia      : {signo}{resumen['diferencia']:,.2f} C$ "
                  f"({resumen['variacion_pct']:+.2f}%)")
            print(f"   Lecturas de capital registradas: {resumen['n_lecturas']}")
        else:
            print("💰 CAPITAL: sin lecturas suficientes. Verifica ConfigGlobal.MONITOR_CAPITAL "
                  "(región de pantalla) y que pytesseract + Tesseract-OCR estén instalados.")

        # 🧠 Memoria de refuerzo (Q-Learning sobre operaciones ganadas/perdidas)
        try:
            pm = self.decision_system.transformer_engine.pattern_memory
            if pm and pm.stats()["total"] > 0:
                st = pm.stats()
                print("-"*80)
                print(f"🧠 REFUERZO Q-LEARNING: {st['total']} operaciones aprendidas "
                      f"({st['ganadas']} ganadas / {st['perdidas']} perdidas) — "
                      f"memoria persistida en {pm.filepath}")
        except Exception:
            pass
        print("="*80)

# =============================================================================
# 📍 EJECUCIÓN PRINCIPAL
# =============================================================================

def main():
    print("\n⚡ INICIANDO SISTEMA HÍBRIDO MULTIFUENTE (TODAS LAS METODOLOGÍAS)")
    print("   Las fuentes de datos gratuitas proporcionan precios reales en tiempo real.")
    print("   En caso de fallo de una fuente, se prueba automáticamente la siguiente.\n")
    try:
        import cv2, numpy, mss, requests
    except ImportError as e:
        print(f"❌ Error: falta {e.name}. Instala: pip install opencv-python numpy mss requests")
        return
    # 🧭 Configuración de coordenadas (gráfico, capital, clicks de compra/venta)
    # ANTES de iniciar el sistema, tal como se pedía.
    configurar_coordenadas_si_necesario()
    sistema = AdvancedTradingSystem()
    print("\n🎮 Controles: [a] Activar trading | [d] Desactivar | [s] Sincronización | [p] Rendimiento | [t] Estado Transformer | [c] Captura | [q] Salir")
    sistema.run_continuous_with_visual()

if __name__ == "__main__":
    main()