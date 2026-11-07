"""Las referencias que guarda el formulario (enlaces) se convierten en el id que pide cada API."""
from app.modulos.evidencias.referencias import base_notion, carpeta_drive, repositorio_github

NOTION_ID = "3ea2ed0da4c3803f9191c8cda25669d4"
DRIVE_ID = "1c3a0gca38gucx-8gLvRylWquokHVmZiX"


def test_github_acepta_url_y_owner_repo():
    url = "https://github.com/jhon1212-beep/taller1-sistema-multiagentes"
    assert repositorio_github(url) == "jhon1212-beep/taller1-sistema-multiagentes"
    assert repositorio_github(url + ".git") == "jhon1212-beep/taller1-sistema-multiagentes"
    assert repositorio_github(url + "/tree/main") == "jhon1212-beep/taller1-sistema-multiagentes"
    assert repositorio_github("jhon1212-beep/taller1-sistema-multiagentes") == "jhon1212-beep/taller1-sistema-multiagentes"
    assert repositorio_github("dataset:1") == "dataset:1"


def test_notion_extrae_el_id_de_la_base():
    assert base_notion(f"https://app.notion.com/p/Base-Demo-Taller-1-{NOTION_ID}?source=copy_link") == NOTION_ID
    assert base_notion(f"https://www.notion.so/espacio/{NOTION_ID}?v=0123456789abcdef0123456789abcdef") == NOTION_ID
    uuid = "3ea2ed0d-a4c3-803f-9191-c8cda25669d4"
    assert base_notion(f"https://www.notion.so/{uuid}") == uuid
    assert base_notion(NOTION_ID) == NOTION_ID


def test_drive_extrae_el_id_de_la_carpeta():
    assert carpeta_drive(f"https://drive.google.com/drive/folders/{DRIVE_ID}?usp=sharing") == DRIVE_ID
    assert carpeta_drive(f"https://drive.google.com/drive/u/0/folders/{DRIVE_ID}") == DRIVE_ID
    assert carpeta_drive(f"https://drive.google.com/open?id={DRIVE_ID}") == DRIVE_ID
    assert carpeta_drive(DRIVE_ID) == DRIVE_ID
