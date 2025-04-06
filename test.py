from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User  # Verifiquem la base de dades
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options  # Fem servir Firferox ESR en comptes de Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class MySeleniumTests(StaticLiveServerTestCase):
    fixtures = ['testdb.json']  # BBDD de prova

    @classmethod
    def setUpClass(cls):
        """Configuració inicial: Obrir Selenium amb Firefox."""
        super().setUpClass()
        opts = Options()
        opts.add_argument("--headless")  # Executem en mode headless (sense interfície gràfica)
        cls.selenium = webdriver.Firefox(options=opts)
        cls.selenium.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        """Tancar Selenium després de les proves."""
        cls.selenium.quit()
        super().tearDownClass()

    def test_login_and_add_user(self):
        """Test per comprovar que el superusuari pot accedir i afegir usuaris."""
        self.selenium.get(f"{self.live_server_url}/admin/login/")

        # Iniciem sessió amb el super usuari
        self.selenium.find_element(By.NAME, "username").send_keys("isard")
        self.selenium.find_element(By.NAME, "password").send_keys("pirineus")
        self.selenium.find_element(By.XPATH, '//input[@value="Log in"]').click()

        # Comprovar que hem iniciat sessió correctament
        self.assertEqual(self.selenium.title, "Site administration | Django site admin")

        # Accedir a la secció d'usuaris
        self.selenium.get(f"{self.live_server_url}/admin/auth/user/")

        # Fer clic a "Add user"
        add_user_link = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@id="content-main"]//a[contains(@href, "/admin/auth/user/add/")]'))
        )
        add_user_link.click()

        # Verificar que estem a la pàgina d’afegir usuari
        self.assertIn("/admin/auth/user/add/", self.selenium.current_url)

        # Omplim el formulari per crear un usuari nou
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        ).send_keys("Sergi")
        self.selenium.find_element(By.NAME, "password1").send_keys("Soler123*")
        self.selenium.find_element(By.NAME, "password2").send_keys("Soler123*")

        # Guardem el nou usuari
        self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()

        # Marquem el camp "is_staff"
        staff_checkbox = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.NAME, "is_staff"))
        )
        if not staff_checkbox.is_selected():
            staff_checkbox.click()

        # Desem els canvis
        self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()

        # Verifiquem que l’usuari s’ha creat correctament a la BBDD
        user = User.objects.filter(username="Sergi").first()
        self.assertIsNotNone(user)  # Comprovem que l'usuari existeix
        self.assertTrue(user.is_staff)  # Comprovem que l'usuari té permisos de staff

    def test_sergi_cannot_create_users(self):
        """Test per comprovar que l'usuari Sergi no pot crear altres usuaris."""

        # 1. Tanquem la sessió del superusuari
        self.selenium.get(f"{self.live_server_url}/admin/logout/")

        # 2. Iniciem sessió amb l'usuari Sergi
        self.selenium.get(f"{self.live_server_url}/admin/login/")
        self.selenium.find_element(By.NAME, "username").send_keys("Sergi")
        self.selenium.find_element(By.NAME, "password").send_keys("Soler123*")
        self.selenium.find_element(By.XPATH, '//input[@value="Log in"]').click()

        # 3. Intentem accedir al menú d'usuaris
        self.selenium.get(f"{self.live_server_url}/admin/auth/user/")
        # Verifiquem que s'ha redireccionat (codi d'estat HTTP 302)
        self.assertEqual(self.selenium.current_url, f"{self.live_server_url}/admin/login/?next=/admin/auth/user/")

        # 4. Intentem accedir a la secció Questions
        self.selenium.get(f"{self.live_server_url}/admin/polls/question/")
        # Verifiquem que s'ha redireccionat (codi d'estat HTTP 302)
        self.assertEqual(self.selenium.current_url, f"{self.live_server_url}/admin/login/?next=/admin/polls/question/")

        # 5. Intentem accedir a la secció de Choices
        self.selenium.get(f"{self.live_server_url}/admin/polls/choice/")
        # Verifiquem que s'ha redireccionat (codi d'estat HTTP 302)
        self.assertEqual(self.selenium.current_url, f"{self.live_server_url}/admin/login/?next=/admin/polls/choice/")
