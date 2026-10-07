"""RN-001: reglas de exclusión y plantilla sin credenciales."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_credenciales_excluidas_y_plantilla_versionable():
    paths = [
        '.env', '.env.local', '.env.production', 'backend/.env',
        'service-account-drive.json', 'config/service-account-demo.json',
        'client_secret_demo.json', 'credentials.json', 'token.json',
        'private.pem', 'private.key',
    ]
    result = subprocess.run(
        ['git', 'check-ignore', '--no-index', '-z', '--stdin'],
        input='\0'.join(paths) + '\0', cwd=ROOT, text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert set(result.stdout.rstrip('\0').split('\0')) == set(paths)
    example = subprocess.run(
        ['git', 'check-ignore', '--no-index', '.env.example'],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert example.returncode == 1, 'La plantilla debe poder versionarse'


def test_variables_sensibles_documentadas_sin_valores():
    values = {}
    for line in (ROOT / '.env.example').read_text(encoding='utf-8').splitlines():
        if line.strip() and not line.lstrip().startswith('#'):
            key, value = line.split('=', 1)
            values[key.strip()] = value.strip()
    required = {
        'GITHUB_TOKEN', 'NOTION_TOKEN', 'GOOGLE_SERVICE_ACCOUNT_JSON',
        'GEMINI_API_KEY', 'LANGSMITH_API_KEY', 'DATABASE_URL',
    }
    assert required <= values.keys()
    assert all(values[key] == '' for key in required), 'Usar valores vacíos en la plantilla'
