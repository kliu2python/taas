from time import sleep

import selenium.webdriver.support.expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait


class LicenseManager:
    def __init__(self, username, password):
        self.driver = None
        self.username = username
        self.password = password
        self.get_driver()

    def get_driver(self):
        parm = {}
        cap = DesiredCapabilities.CHROME
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument('--ignore-certificate-errors')
        driver = webdriver.Chrome
        parm["desired_capabilities"] = cap
        parm["options"] = options

        self.driver = driver(**parm)

    def find_element(
            self, by, locator, timeout=10, method=ec.presence_of_element_located
    ):
        retry = 3
        while retry > 0:
            try:
                wait = WebDriverWait(self.driver, timeout)
                return wait.until(
                    method((by, locator))
                )
            except Exception as e:
                print(e)
                retry -= 1
                if retry <= 0:
                    raise e
                sleep(3)

    def login(self):
        self.driver.get("https://support.fortinet.com/asset/#/")
        ele = self.find_element(By.NAME, "username")
        ele.click()
        ele.send_keys(self.username)

        ele = self.find_element(By.NAME, "password")
        ele.click()
        ele.send_keys(self.password)

        ele = self.find_element(By.XPATH, "//input[@value = 'LOGIN']")
        ele.click()

    def _click_button_contains_text(self, text):
        ele = self.find_element(
            By.XPATH, f"//button[contains(text(), '{text}')]"
        )
        ele.click()

    def register_device(self, reg_code, ip):
        ele = self.find_element(By.XPATH, "//span[text()='Dashboard']")
        ele.click()

        ele = self.find_element(
            By.XPATH, "//*[contains(text(), 'Register Now')]"
        )
        ele.click()

        ele = self.find_element(By.XPATH, "//*[@value='NonGovernmentUser']")
        ele.click()
        ele = self.find_element(By.ID, "RegNumber")
        ele.send_keys(reg_code)
        self._click_button_contains_text("Next")

        ele = self.find_element(
            By.XPATH, "//span[contains(text(), 'Select a Partner')]"
        )
        ele.click()
        ele = self.find_element(By.XPATH, "//div[contains(text(), 'Unknown')]")
        ele.click()
        ele = self.find_element(
            By.XPATH,
            "//*[*[*[contains(text(), 'IP Address')]]]/div[2]/div/input"
        )
        ele.click()
        ele.send_keys(ip)
        self._click_button_contains_text("Next")

        ele = self.find_element(By.XPATH, "//input[@type='checkbox']")
        ele.click()

        self._click_button_contains_text("Confirm")

        ele = self.find_element(
            By.XPATH,
            "//a[contains(text(), 'License File Download')]",
            timeout=30
        )
        ele.click()

        ele = self.find_element(
            By.XPATH,
            "//*[*[*[contains(text(), 'Serial Number')]]]//span"
        )
        return ele.text

    def close(self):
        self.driver.close()


if __name__ == "__main__":
    manager = LicenseManager("ftc.manual.znie@gmail.com", "xxxx")
    manager.login()
    manager.register_device("3L5QX-ZCW3K-7UK1B-KP94H-G2B85B", "10.1.1.2")
    manager.close()
