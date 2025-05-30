import os
import yaml
from app import load_config

def test_load_config_defaults(tmp_path, monkeypatch):
    # Brak pliku config.yaml -> domyślne wartości
    monkeypatch.chdir(tmp_path)
    config = load_config()
    assert isinstance(config, dict)
    assert 'output_dir' in config
    assert 'log_level' in config
    assert 'ocr_lang' in config

def test_load_config_custom(tmp_path, monkeypatch):
    # Plik config.yaml z niestandardowymi wartościami
    config_path = tmp_path / 'config.yaml'
    config_data = {
        'output_dir': '~/TestOutput',
        'log_level': 'DEBUG',
        'ocr_lang': 'eng',
    }
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f)
    monkeypatch.chdir(tmp_path)
    config = load_config()
    expected_dir = os.path.expanduser('~/TestOutput')
    assert os.path.abspath(config['output_dir']) == os.path.abspath(expected_dir)
    assert config['log_level'] == 'DEBUG'
    assert config['ocr_lang'] == 'eng'
