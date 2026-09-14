# text_review.py
# LLM이 쓴 문구(타임라인 브리핑·해설, 보고서)를 저장 전에 코드로 검사한다. LLM을 부르지 않는다.
#   normalize_percent  숫자 뒤 "퍼센트" -> "%"
#   rule_issues        코드로 판단할 수 있는 문제 목록 (자료에 없는 숫자, 비교 표현, 애프터마켓 등락률 기준)
#   check              원고에 확실한 자동 수정(퍼센트 표기, "홀로"·"유일하게" 삭제)을 적용하고, 남은 문제를 WARNING 로그로 남긴다
# 원인을 지어낸 문장처럼 코드로 판단할 수 없는 오류는 잡지 못한다 -> 저장 후 자료와 대조해 확인한다

import logging
import re

logger = logging.getLogger(__name__)

# 숫자 뒤 "퍼센트"를 "%"로 바꾼다. 프롬프트로 금지해도 LLM이 가끔 "17.67퍼센트"로 쓴다
_PERCENT_WORD = re.compile(r"(\d)\s*퍼센트")

# 원고 속 숫자 (쉼표·소수점 포함)
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")

# 다른 대상과 비교해야 쓸 수 있는 표현. 코드가 비교를 확인할 수 없어 원고에서 지운다 (뒤 공백 포함)
# 지워도 문장이 성립하는 말만 넣는다 ("하락장 속 홀로 상승" -> "하락장 속 상승")
_COMPARE_WORDS = re.compile(r"(나홀로|홀로|유일하게)\s*")

# 지운 뒤 연달아 생긴 공백
_SPACES = re.compile(r" {2,}")

# 정규장 상승분을 애프터마켓 상승으로 쓴 문장 (17:30·20:00 급상승 종목 등락률은 전일 종가 대비다)
# 같은 문장 안에서만 찾는다 (문장 끝 = 마침표·물음표·느낌표 뒤 공백 또는 끝. "29.91"의 소수점은 문장 끝이 아니다)
_AFTERMARKET_RISE = re.compile(r"애프터마켓에서(?:(?![.!?](?:\s|$)).)*?(올랐|오른|올라|오르며|상승했|상승한|상승하며|급등했|급등한|급등하며|뛰었|뛴)")

# 검사하지 않는 키 (태그는 단어 목록이라 문장이 아니다)
_SKIP_KEYS = {"tags"}


def normalize_percent(text: str) -> str:
    return _PERCENT_WORD.sub(r"\1%", text)


# 원고 dict·list 안의 문자열을 전부 꺼낸다
def _texts(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for key, item in value.items() if key not in _SKIP_KEYS for text in _texts(item)]
    if isinstance(value, list):
        return [text for item in value for text in _texts(item)]
    return []


# 원고 속 숫자 중 자료에 없는 것. 자료에 같은 숫자 문자열이 있거나, 자료 숫자를 원고 자릿수로 반올림·버림하면 같으면 통과
#   (자료 1.23 -> 원고 1.2, 자료 "-2조 2,984억원" -> 원고 "2조 2,984억원")
# 두 자리 이하 정수는 날짜·개수·"3%대"처럼 흔해서, 1900~2099 네 자리 정수는 연도라서 검사하지 않는다
def _unknown_numbers(text: str, plain_source: str, source_numbers: list[float]) -> list[str]:
    unknown = []
    for match in _NUMBER.finditer(text):
        raw = match.group().rstrip(",").replace(",", "")
        if not raw or raw in plain_source or ("." not in raw and (len(raw) <= 2 or (len(raw) == 4 and raw[:2] in ("19", "20")))):
            continue
        value = float(raw)
        decimals = len(raw.split(".")[1]) if "." in raw else 0
        if any(round(abs(number), decimals) == value or int(abs(number) * 10**decimals) / 10**decimals == value for number in source_numbers):
            continue
        start = max(0, match.start() - 20)
        unknown.append(f"자료에 없는 숫자 '{match.group()}' (…{text[start:match.end() + 20]}…)")
    return unknown


# 코드로 판단할 수 있는 문제 목록
#   texts             검사할 문구들
#   source            LLM에 준 자료 전체 (JSON 문자열)
#   aftermarket_basis True면 "애프터마켓에서 OO% 올랐다" 표현을 잡는다 (17:30·20:00 슬롯)
def rule_issues(texts: list[str], source: str, *, aftermarket_basis: bool = False) -> list[str]:
    plain_source = source.replace(",", "")
    source_numbers = [float(raw.replace(",", "")) for raw in _NUMBER.findall(source) if raw.replace(",", "")]
    issues = []
    for text in texts:
        issues.extend(_unknown_numbers(text, plain_source, source_numbers))
        if _COMPARE_WORDS.search(text):
            issues.append(f"비교 표현 (…{text[:60]}…)")
        if aftermarket_basis and _AFTERMARKET_RISE.search(text):
            issues.append(f"애프터마켓 상승으로 쓴 전일 대비 등락률 (…{text[:60]}…)")
    return issues


# 문자열 하나에 자동 수정을 적용한다
def _fixed(text: str) -> str:
    return _SPACES.sub(" ", _COMPARE_WORDS.sub("", normalize_percent(text.strip()))).strip()


def _apply(value):
    if isinstance(value, str):
        return _fixed(value)
    if isinstance(value, dict):
        return {key: (item if key in _SKIP_KEYS else _apply(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [_apply(item) for item in value]
    return value


# 원고에 자동 수정을 적용한 사본을 돌려주고, 수정한 것과 남은 문제를 로그로 남긴다 (모양은 원고와 같다)
#   label   로그에 찍을 이름 (예: "20:00 브리핑·해설", "DAILY 2026-09-14 보고서")
#   draft   원고 (문자열·목록·dict. "tags" 키는 검사하지 않는다)
#   source  원고를 쓸 때 LLM에 준 자료 (JSON 문자열)
def check(label: str, draft, source: str, *, aftermarket_basis: bool = False):
    before = _texts(draft)
    result = _apply(draft)
    after = _texts(result)

    changed = [f"{old} -> {new}" for old, new in zip(before, after) if _COMPARE_WORDS.search(old)]
    if changed:
        logger.info("%s 비교 표현 삭제 %d건: %s", label, len(changed), " / ".join(changed))

    issues = rule_issues(after, source, aftermarket_basis=aftermarket_basis)
    if issues:
        logger.warning("%s 자동 검사 문제 %d건 (저장 후 확인 필요): %s", label, len(issues), " / ".join(issues))
    return result
