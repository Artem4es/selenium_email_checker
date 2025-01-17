import logging
import threading
from typing import Final

from seleniumwire import webdriver
from seleniumwire.request import Request
from selenium.common.exceptions import NoSuchDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait, WebDriver
from selenium.webdriver.support import expected_conditions as EC

# Proxy addresses
NO_ROTATION_PROXY_HTTP: Final[str] = (
    "http://0iyLsMBhVIRtEBuqLoSS:RNW78Fm5@185.162.130.86:10000"
)
NO_ROTATION_PROXY_SOCK5: Final[str] = (
    "socks5://1w298ZXlKuonHdkwiyVV:RNW78Fm5@185.162.130.86:10000"
)

ROTATION_PROXY_HTTP: Final[str] = (
    "http://Hn4xF9GAy4YmJMPltBNC:RNW78Fm5@185.162.130.86:10000"
)
ROTATION_PROXY_SOCK5: Final[str] = (
    "socks5://7e8Lldby4Fn2Nhf0iXCa:RNW78Fm5@185.162.130.86:10000"
)

# Test data
REGISTER_URL: Final[str] = "https://member.aorus.com/global/register"
CONTROL_URL_PART: Final[str] = "chk_email_registered"
CONTROL_PHRASE: Final[str] = "Email address already in use."
EMAIL_ONE: Final[str] = "tutazatuta@tutamail.com"
EMAIL_TWO: Final[str] = "a@b.ru"
TEST_NICKNAME: Final[str] = "super_nickname"
PASSWORD: Final[str] = "SuperSecretPass123!"

# Selenium settings
SELENIUM_EXECUTABLE: Final[str] = "/usr/bin/chromium-browser"
SELENIUMWIRE_OPTIONS: Final[dict] = {
    "request_storage": "memory",
    "disable_encoding": True,
    "ignore_http_methods": [],
    "connection_timeout": None,
}
MAX_WAITING_TIME: Final[int] = 10

# Web form fields
EMAIL_FIELD: Final[str] = "email"
NICKNAME_FIELD: Final[str] = "User_Name"
PASS_FIELD: Final[str] = "password"
PASS_CONFIRM_FIELD: Final[str] = "password_confirmation"
CONFIRM_BUTTON: Final[str] = "GA-Signup-Next"

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.CRITICAL)


def checker(email: str, proxy: str | None) -> bool | None:
    """Check if an email is already registered."""
    try:
        driver = _prepare_webdriver(proxy)
        driver.get(REGISTER_URL)

        driver.find_element(By.NAME, EMAIL_FIELD).send_keys(email)
        driver.find_element(By.NAME, NICKNAME_FIELD).send_keys(TEST_NICKNAME)
        driver.find_element(By.NAME, PASS_FIELD).send_keys(PASSWORD)
        driver.find_element(By.NAME, PASS_CONFIRM_FIELD).send_keys(PASSWORD)
        driver.find_element(By.CLASS_NAME, CONFIRM_BUTTON).click()

        WebDriverWait(driver, MAX_WAITING_TIME).until(
            lambda d: any(CONTROL_URL_PART in r.url and r.response for r in d.requests)
        )
        target_request = _get_target_request(driver.requests, target=CONTROL_URL_PART)
        response_text = target_request.response.body.decode()
        res = response_text == CONTROL_PHRASE
        log.critical("Результат для email %s: %s", email, res)
        return res

    except NoSuchDriverException as e:
        log.critical("Выбран несуществующий драйвер Selenium: %s", str(e))

    except TimeoutException:
        log.critical("Запрос занял слишком много... '%s'.", email)
        log.critical("Результат для email %s: %s", email, None)

    except Exception as e:
        log.critical("Неизвестная ошибка для email '%s': %r", email, e)
        log.critical("Результат для email %s: %s", email, None)


def _prepare_webdriver(proxy: str | None) -> WebDriver:
    """Prepare a Selenium WebDriver with proxy and options."""
    options = webdriver.ChromeOptions()
    options.binary_location = SELENIUM_EXECUTABLE
    options.add_argument("--headless")
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")

    return webdriver.Chrome(seleniumwire_options=SELENIUMWIRE_OPTIONS, options=options)


def _get_target_request(requests: list[Request], target: str) -> Request | None:
    """Find a request by a substring in its URL."""
    return next((req for req in requests if target in req.url), None)


def main() -> None:
    threads = [
        threading.Thread(target=checker, args=(EMAIL_ONE, ROTATION_PROXY_HTTP)),
        threading.Thread(target=checker, args=(EMAIL_TWO, NO_ROTATION_PROXY_SOCK5)),
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
