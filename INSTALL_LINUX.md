# 🐧 Instalação no Linux (Ubuntu/Debian)

## Pré-requisitos

### 1. Instalar dependências do sistema

```bash
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-dev \
    tesseract-ocr \
    tesseract-ocr-por \
    python3-pyqt5 \
    python3-xlib \
    xdotool \
    build-essential \
    libx11-dev \
    libxtst-dev
```

### 2. Instalar pacotes Python

```bash
pip3 install -r requirements.txt
```

## Permissões necessárias

### Acesso à memória de processos

Para ler a memória de outros processos no Linux, você precisa de permissões especiais:

**Opção 1: Executar como root (não recomendado para uso diário)**
```bash
sudo python3 StartBot.py
```

**Opção 2: Configurar ptrace (mais seguro)**
```bash
# Permitir ptrace para processos do mesmo usuário
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope

# Para tornar permanente, adicione ao /etc/sysctl.conf:
echo "kernel.yama.ptrace_scope = 0" | sudo tee -a /etc/sysctl.conf
```

**Opção 3: Adicionar capabilities ao Python (recomendado)**
```bash
# Dar permissão ao Python para acessar memória de processos
sudo setcap cap_sys_ptrace=eip /usr/bin/python3.10

# Verificar
getcap /usr/bin/python3.10
```

### Acesso ao servidor X11

Para simular entrada de teclado/mouse, você pode precisar configurar permissões do X11:

```bash
# Permitir conexões locais ao X11
xhost +local:
```

## Executar o bot

```bash
python3 StartBot.py
```

## Solução de problemas

### Erro: "No module named 'Xlib'"
```bash
pip3 install python-xlib
```

### Erro: "Operation not permitted" ao ler memória
- Verifique se configurou ptrace conforme acima
- Ou execute como root: `sudo python3 StartBot.py`

### Erro: "tesseract: command not found"
```bash
sudo apt install tesseract-ocr
```

### Interface gráfica não aparece
```bash
# Instale o PyQt5
sudo apt install python3-pyqt5
```

### Cliente Tibia não é detectado

Certifique-se de que:
1. O cliente está rodando
2. A janela está visível (não minimizada)
3. Você tem permissões para acessar o processo

## Notas importantes

### Diferenças entre Windows e Linux

1. **Leitura de memória**: No Linux usa `process_vm_readv` em vez de `ReadProcessMemory`
2. **Simulação de entrada**: Usa Xlib/XTest em vez de PostMessage do Windows
3. **Captura de tela**: Usa Xlib para captura em vez de GDI do Windows
4. **Permissões**: Linux requer configuração de ptrace

### Limitações no Linux

- A simulação de entrada pode não funcionar em Wayland (use X11)
- Alguns clientes OT com proteção podem não funcionar
- Performance pode variar dependendo da distribuição

### Wine/Proton

Se estiver rodando o cliente Tibia via Wine:
```bash
# O bot pode não conseguir acessar processos Wine diretamente
# Considere rodar o bot também via Wine:
wine python StartBot.py
```

## Desenvolvimento

Para contribuir com melhorias específicas do Linux:

1. Os arquivos multiplataforma estão em `Platform/PlatformAbstraction.py`
2. Testes devem funcionar tanto no Windows quanto no Linux
3. Use `IS_WINDOWS` e `IS_LINUX` para lógica específica de plataforma

## Suporte

Para problemas específicos do Linux, abra uma issue no GitHub com:
- Distribuição Linux e versão
- Logs de erro completos
- Versão do Python (`python3 --version`)
- Saída de `pip3 list | grep -i "xlib\|pyqt"`
