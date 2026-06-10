import yaml

def read_yaml(yaml_path):
    """读取 YAML 文件内容"""
    with open(yaml_path, mode='r', encoding='utf-8') as f:
        value = yaml.load(f, Loader=yaml.FullLoader)
        return value
