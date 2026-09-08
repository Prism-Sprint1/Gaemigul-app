from fastapi import FastAPI

# FastAPI 인스턴스 생성
app = FastAPI()


# 기본 헬스 체크 엔드 포인트
@app.get("/")
def read_root():
    return {"message": "hello world"}
