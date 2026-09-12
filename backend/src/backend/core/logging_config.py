# logging_config.py
# 로그 설정 (전 도메인 공용)
#
# 왜 print를 쓰지 않는가
#   print는 터미널에만 남는다. 서버를 닫으면 사라지고, 스크롤을 넘기면 못 찾는다.
#   실제로 2026-09-11에 슬롯 3개가 저장 직전에 실패했는데, 터미널이 이미 지나가서
#   원인을 찾는 데 한참 걸렸다. 실데이터를 쌓기 시작하면 이런 일이 반복된다.
#
#   프로젝트 필수 구현 사항에도 '예외 처리 및 오류 로깅'이 있다.
#
# 어디에 남는가
#   1. 터미널 - 전에 print로 보던 것과 같게 보인다 (개발 중 확인용)
#   2. backend/logs/timeline.log - 자정에 날짜를 붙여 넘기고 14일치를 보관한다
#      (timeline.log.2026-09-14 형태). logs 폴더는 git에 올리지 않는다
#
# 레벨 기준
#   DEBUG    쓰지 않는다. 필요해지면 단계별 소요 시간을 여기로 내리면 된다
#   INFO     정상 흐름. 수집 시작·완료, 휴장일 건너뜀, 기존 브리핑 유지
#   WARNING  일부가 실패했지만 슬롯은 만들어진 경우. LLM 실패, 뉴스 선별 실패,
#            휴장일 조회 실패, 07:30 슬롯 없어서 장중 변화 못 만든 경우
#   ERROR    슬롯이 통째로 실패한 경우. 예외 스택도 같이 남긴다
#
#   운영 중에 무슨 일이 있었는지는 WARNING 이상만 보면 된다.
#     grep -E "WARNING|ERROR" logs/timeline.log
#
# 쓰는 법
#   파일 맨 위에서 logger를 하나 만들고 print 대신 부른다.
#     logger = logging.getLogger(__name__)
#     logger.warning("브리핑 생성 실패 - %s", error)
#   메시지에 f-string을 쓰지 않고 %s로 넘기는 편이 좋다. 그 레벨이 꺼져 있으면
#   문자열을 만드는 비용조차 들지 않는다

import logging
import time
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from zoneinfo import ZoneInfo

_KST = ZoneInfo("Asia/Seoul")

# 로그 파일 위치. backend/logs/timeline.log
# (이 파일이 backend/src/backend/core/ 에 있으므로 세 단계 위가 backend/)
LOG_DIR = Path(__file__).resolve().parents[3] / "logs"
LOG_FILE = LOG_DIR / "timeline.log"

# 보관 기간(일). 자정마다 날짜를 붙여 넘기고 이만큼만 남긴다
_BACKUP_DAYS = 14

# 로거 이름은 %(name)s 대신 %(module)s(파일명)를 쓴다.
# %(name)s은 "backend.domain.timeline.services.timeline_service"처럼 48자가 넘어서
# 한 줄에서 정작 봐야 할 메시지를 밀어낸다. 파일명만으로도 어디서 났는지 충분히 안다
_FORMAT = "%(asctime)s %(levelname)-7s %(module)-22s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 시끄러운 외부 로거. 이 밑으로는 경고만 본다
#   httpx        요청마다 INFO를 한 줄씩 남긴다. 슬롯 하나에 KIS·네이버·제미나이를 수십 번 부른다
#   apscheduler  작업을 등록할 때마다 두 줄씩 남긴다. 작업이 9개라 서버를 켤 때마다 18줄이 찍힌다
#                (실측: 로그 23줄 중 19줄이 이것이었다)
#
# WARNING 이상은 남겨둔다. apscheduler의 경고·오류는 반드시 봐야 하는 것들이다.
#   - 예약 시각을 놓쳤을 때 ("Run time of job ... was missed by ...") - misfire_grace_time이 10초라
#     맥이 잠들었다 깨면 여기 걸린다
#   - 작업 안에서 예외가 터졌을 때
_QUIET_LOGGERS = {
    "httpx": logging.WARNING,
    "httpcore": logging.WARNING,
    "apscheduler": logging.WARNING,
}

_configured = False


# 로그 시각을 한국 시간으로 찍는다
#
# 굳이 명시하는 이유: 기본값은 서버가 놓인 기기의 지역 시간이다. 지금은 맥이 한국 시간이라
# 그대로도 맞지만, 다른 환경에서 돌리면 로그 시각과 DB의 time_slot이 어긋난다.
# 이 프로젝트는 시간대 불일치로 이미 여러 번 헤맸으므로 여기서 못박아둔다
def _kst_converter(timestamp: float) -> time.struct_time:
    from datetime import datetime

    return datetime.fromtimestamp(timestamp, _KST).timetuple()


# 로그 설정을 한 번만 적용한다 (서버 기동 시 main.py가 부른다)
#
# 스크립트로 따로 실행할 때도 부르면 같은 파일에 남는다.
# 두 번 불러도 핸들러가 중복되지 않도록 막아뒀다 - 중복되면 같은 줄이 두 번씩 찍힌다
def setup_logging(level: int = logging.INFO) -> None:
    global _configured
    if _configured:
        return

    formatter = logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT)
    formatter.converter = _kst_converter

    handlers: list[logging.Handler] = [logging.StreamHandler()]

    # 파일 핸들러는 실패해도 앱을 막지 않는다 (쓰기 권한이 없는 환경이 있을 수 있다)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        handlers.append(
            TimedRotatingFileHandler(LOG_FILE, when="midnight", backupCount=_BACKUP_DAYS, encoding="utf-8")
        )
    except OSError as error:
        print(f"[경고] 로그 파일을 만들 수 없어 터미널에만 남깁니다 - {error}")

    root = logging.getLogger()
    root.setLevel(level)
    for handler in handlers:
        handler.setFormatter(formatter)
        root.addHandler(handler)

    for name, quiet_level in _QUIET_LOGGERS.items():
        logging.getLogger(name).setLevel(quiet_level)

    _configured = True
    logging.getLogger(__name__).info("로그 설정 완료 - %s (보관 %d일)", LOG_FILE, _BACKUP_DAYS)
