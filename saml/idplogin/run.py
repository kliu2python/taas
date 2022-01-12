import os

from datetime import datetime
from concurrent.futures import ProcessPoolExecutor

from samlclient import SamlClient

CONCURRENT = int(os.environ.get("CONCURRENT", 1))
REPEAT = int(os.environ.get("REPEAT", 10000000000))
PASSWORD = os.environ.get("PASSWORD", "fortinet")
URL = os.environ.get("URL", "https://10.160.13.220:10001")
USER_PREFIX = os.environ.get("USER_PREFIX", "idptest")
LOGOUT = os.environ.get("LOGOUT", "yes") == "yes"


class LoginFailError(Exception):
    pass


def login(url, user, password, repeat):
    done = 0
    success = 0
    fail = 0
    while done < repeat:
        try:
            login_fail = True
            context, token = SamlClient.login(url, user, password)
            if context.status_code == 200:
                if LOGOUT:
                    context = SamlClient.logout(context, token)
                if context.status_code == 200:
                    success += 1
                    login_fail = False

            if login_fail:
                print(context.status_code)
                print(context.content)
                raise LoginFailError(
                    f"{context.status_code}, {context.content}"
                )
        except Exception as e:
            print(e)
            fail += 1
        finally:
            done += 1

    return [done, success, fail]


if __name__ == '__main__':
    result = []
    t1 = datetime.now().timestamp()
    with ProcessPoolExecutor(max_workers=CONCURRENT) as pool:
        for i in range(CONCURRENT):
            future = pool.submit(
                login,
                url=URL,
                user=f"{USER_PREFIX}{i + 1}",
                password=PASSWORD,
                repeat=REPEAT
            )
            result.append(future)
    t2 = datetime.now().timestamp()
    total_time = t2 - t1
    total_call = 0
    for res in result:
        result = res.result()
        total_call += result[0]
        print(result)
    print(f"Total time: {total_time} seconds")
    print(f"Average call time: {total_time/total_call * 1000} ms")
