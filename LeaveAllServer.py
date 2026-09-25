import sys
import time
import requests

API_BASE = "https://discord.com/api/v9"
HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json"
}

# 콘솔 색상
C_GREEN = "\033[92m"
C_RED = "\033[91m"
C_YELLOW = "\033[93m"
C_RESET = "\033[0m"


class DiscordClient:
    def __init__(self, token):
        self.session = requests.Session()
        self.session.headers.update(HEADERS_BASE)
        self.session.headers["Authorization"] = token.strip()
        self.guilds = []

    def check_auth(self):
        # 토큰 유효성 및 본인 계정 확인
        res = self.session.get(f"{API_BASE}/users/@me")
        if res.status_code == 200:
            user = res.json()
            tag = f"{user.get('username')}#{user.get('discriminator', '0')}"
            print(f"{C_GREEN}[+] 계정 확인 완료: {tag}{C_RESET}")
            return True
        print(f"{C_RED}[-] 로그인 실패: HTTP {res.status_code}{C_RESET}")
        return False

    def load_guilds(self):
        # 참여 중인 서버 목록 로드
        res = self.session.get(f"{API_BASE}/users/@me/guilds")
        if res.status_code == 200:
            self.guilds = res.json()
            return self.guilds
        elif res.status_code == 429:
            retry_wait = res.json().get("retry_after", 5)
            print(f"{C_YELLOW}[!] API 지연 발생, {retry_wait}초 대기{C_RESET}")
            time.sleep(retry_wait + 0.5)
            return self.load_guilds()
        return []

    def leave_server(self, guild_id, name=""):
        url = f"{API_BASE}/users/@me/guilds/{guild_id}"
        
        while True:
            # POST 대신 DELETE 메서드 호출
            res = self.session.delete(url, json={})

            if res.status_code in (200, 204):
                print(f"{C_GREEN}[ok] 나감: {name} ({guild_id}){C_RESET}")
                return True
            
            # 레이트 리밋 처리
            if res.status_code == 429:
                wait_sec = res.json().get("retry_after", 3)
                print(f"{C_YELLOW}[!] 레이트 리밋 걸림. {wait_sec}초 대기 후 재시도...{C_RESET}")
                time.sleep(wait_sec + 0.5)
                continue

            # 소유권이 있거나 권한 부족
            if res.status_code == 403:
                print(f"{C_RED}[err] 서버 소유권이 있어서 탈퇴 안됨: {name}{C_RESET}")
                return False

            # 이미 나갔거나 유효하지 않은 ID
            if res.status_code in (400, 404):
                print(f"{C_YELLOW}[!] 이미 나갔거나 없는 서버: {name}{C_RESET}")
                return True

            print(f"{C_RED}[err] 처리 실패: {res.status_code} ({name}){C_RESET}")
            return False


def main():
    token = input("디스코드 토큰 입력: ").strip()
    if not token:
        print("토큰이 비어있습니다.")
        return

    client = DiscordClient(token)
    if not client.check_auth():
        return

    servers = client.load_guilds()
    if not servers:
        print("참여 중인 서버가 없거나 목록을 불러오지 못했습니다.")
        return

    print(f"\n총 {len(servers)}개 서버 확인됨:")
    for i, g in enumerate(servers, 1):
        owner_flag = " (서버장)" if g.get("owner") else ""
        print(f"[{i}] {g.get('name')} | {g.get('id')}{owner_flag}")

    print("\n--- 작업 선택 ---")
    print("1: 전체 서버 나가기 (본인 소유 서버 제외)")
    print("2: 특정 서버만 나가기")
    print("3: 특정 서버 제외하고 전부 나가기 (화이트리스트)")
    print("4: 종료")

    sel = input("선택 (1~4): ").strip()

    if sel == "1":
        chk = input("정말로 모든 서버를 나가시겠습니까? (y/n): ").strip().lower()
        if chk != "y":
            print("취소되었습니다.")
            return

        delay_input = input("요청 딜레이 초 (기본값 1.5): ").strip()
        delay = float(delay_input) if delay_input else 1.5

        left_cnt = 0
        for g in servers:
            if g.get("owner"):
                continue
            if client.leave_server(g["id"], g.get("name", "")):
                left_cnt += 1
            time.sleep(delay)

        print(f"\n작업 완료. 탈퇴 성공: {left_cnt}개")

    elif sel == "2":
        raw_ids = input("나갈 서버 ID들을 쉼표(,)로 구분해서 입력: ").strip()
        targets = [x.strip() for x in raw_ids.split(",") if x.strip()]
        
        name_map = {g["id"]: g.get("name", "") for g in servers}
        for gid in targets:
            client.leave_server(gid, name_map.get(gid, "알 수 없음"))
            time.sleep(1.0)

    elif sel == "3":
        raw_wl = input("남겨둘(화이트리스트) 서버 ID들을 쉼표(,)로 구분해서 입력: ").strip()
        whitelist = set(x.strip() for x in raw_wl.split(",") if x.strip())

        left_cnt = 0
        for g in servers:
            gid = g["id"]
            if gid in whitelist or g.get("owner"):
                print(f"건너뜀: {g.get('name')}")
                continue

            if client.leave_server(gid, g.get("name", "")):
                left_cnt += 1
            time.sleep(1.5)

        print(f"\n작업 완료. 탈퇴 성공: {left_cnt}개")

    else:
        print("종료합니다.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n강제 종료되었습니다.")
        sys.exit(0)
