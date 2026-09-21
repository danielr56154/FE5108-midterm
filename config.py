"""Tickers and locked choices for FE 5108 Track A."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
EXHIBITS = ROOT / "exhibits"

START = "2016-09-01"
MIN_OBS = 96
RF_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=IRSTCI01JPM156N"
# Yahoo has no TOPIX index ticker; 1306.T (Nomura) has a 10x March-2026 glitch.
# 1305.T is the Daiwa full-TOPIX ETF, same 121 months as the stocks.
MARKET = "1305.T"
# Stage 4 Roll proxy: MSCI World in yen. URTH is USD; JPY=X is USDJPY.
WORLD = "URTH"
FX = "JPY=X"

# TOPIX Core 30 (JPX Oct 2025), minus 8729.T / 9434.T (too little history),
# plus 4689.T LY (Yahoo Japan) to keep N=30.
UNIVERSE = [
    ("2914.T", "Japan Tobacco", "Foods"),
    ("3382.T", "Seven & i", "Retail"),
    ("4063.T", "Shin-Etsu", "Chemicals"),
    ("4502.T", "Takeda", "Pharma"),
    ("4568.T", "Daiichi Sankyo", "Pharma"),
    ("4689.T", "LY (Yahoo)", "Info"),
    ("6098.T", "Recruit", "Services"),
    ("6367.T", "Daikin", "Machinery"),
    ("6501.T", "Hitachi", "Electric"),
    ("6503.T", "Mitsubishi Electric", "Electric"),
    ("6758.T", "Sony", "Electric"),
    ("6857.T", "Advantest", "Electric"),
    ("6861.T", "Keyence", "Electric"),
    ("7011.T", "MHI", "Machinery"),
    ("7203.T", "Toyota", "Autos"),
    ("7267.T", "Honda", "Autos"),
    ("7741.T", "HOYA", "Precision"),
    ("7974.T", "Nintendo", "Other"),
    ("8001.T", "Itochu", "Trading"),
    ("8031.T", "Mitsui", "Trading"),
    ("8035.T", "Tokyo Electron", "Electric"),
    ("8058.T", "Mitsubishi Corp", "Trading"),
    ("8306.T", "MUFG", "Banks"),
    ("8316.T", "SMFG", "Banks"),
    ("8411.T", "Mizuho", "Banks"),
    ("8766.T", "Tokio Marine", "Insurance"),
    ("9432.T", "NTT", "Info"),
    ("9433.T", "KDDI", "Info"),
    ("9983.T", "Fast Retailing", "Retail"),
    ("9984.T", "SoftBank Group", "Info"),
]

TICKERS = [t for t, _, _ in UNIVERSE]
NAMES = {t: n for t, n, _ in UNIVERSE}

# Ken French Japan 3-factor file (USD). Use SMB and HML only — not Mkt-RF / RF.
FF_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Japan_3_Factors_CSV.zip"

# Homemade 12-1 WML needs a year of prices before the first test month.
MOM_START = "2015-09-01"

# Extra TSE names for the WML sort. Thin tapes are dropped at download.
# Core 30 is included automatically; this list is Large/Mid names with long history.
SORT_EXTRA = [
    "1605.T", "1925.T", "2413.T", "2502.T", "2802.T", "3402.T", "3659.T",
    "4452.T", "4503.T", "4519.T", "4543.T", "4661.T", "4755.T", "4901.T",
    "5108.T", "5401.T", "5802.T", "6146.T", "6273.T", "6301.T", "6326.T",
    "6594.T", "6702.T", "6752.T", "6902.T", "6920.T", "6954.T", "6981.T",
    "7201.T", "7270.T", "7309.T", "7733.T", "7751.T", "7832.T", "8002.T",
    "8053.T", "8113.T", "8267.T", "8473.T", "8591.T", "8604.T", "8725.T",
    "8750.T", "8802.T", "9020.T", "9104.T", "9531.T", "9735.T",
]
