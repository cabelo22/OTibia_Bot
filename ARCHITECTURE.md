# Arquitetura Multi-plataforma do OTibia Bot

## Visão Geral

O OTibia Bot foi refatorado para suportar Windows e Linux através de uma camada de abstração unificada. Esta arquitetura permite que o mesmo código funcione em ambas as plataformas sem modificações.

## Estrutura

```
OTibia_Bot/
├── Platform/
│   └── PlatformAbstraction.py    # Camada de abstração multi-plataforma
├── Functions/
│   ├── MemoryFunctions.py        # Operações de memória (usa abstração)
│   ├── MouseFunctions.py         # Simulação de mouse (usa abstração)
│   ├── KeyboardFunctions.py      # Simulação de teclado (usa abstração)
│   └── GeneralFunctions.py       # Funções gerais (usa abstração)
├── General/
│   └── SelectTibiaTab.py         # Seleção de processos (usa abstração)
└── StartBot.py                   # Ponto de entrada (multi-plataforma)
```

## Componentes

### 1. Platform/PlatformAbstraction.py

Fornece APIs unificadas para:

#### MemoryAPI
- `read_process_memory()`: Lê memória de processos
  - **Windows**: `ReadProcessMemory` via kernel32
  - **Linux**: `process_vm_readv` via libc
- `open_process()`: Abre handle de processo
  - **Windows**: `OpenProcess` retorna HANDLE
  - **Linux**: Retorna PID diretamente
- `enable_debug_privilege()`: Habilita privilégios de depuração
  - **Windows**: Ajusta privilégios de token
  - **Linux**: Não necessário (usa ptrace)

#### WindowAPI
- `find_window()`: Encontra janela por título
  - **Windows**: `FindWindow` via win32gui
  - **Linux**: Enumera janelas via Xlib
- `enum_windows()`: Enumera todas as janelas
  - **Windows**: `EnumWindows`
  - **Linux**: `_NET_CLIENT_LIST` via Xlib
- `get_window_thread_process_id()`: Obtém PID da janela
  - **Windows**: `GetWindowThreadProcessId`
  - **Linux**: `_NET_WM_PID` property

#### InputAPI
- `post_message()`: Envia eventos de entrada
  - **Windows**: `PostMessage` com WM_* messages
  - **Linux**: XTest extension para simular eventos
- `get_async_key_state()`: Verifica estado de tecla
  - **Windows**: `GetAsyncKeyState`
  - **Linux**: `query_keymap` via Xlib
- `make_long()`: Combina coordenadas em LPARAM
  - Multiplataforma: bit shifting

#### ScreenCaptureAPI
- `capture_window()`: Captura região da janela
  - **Windows**: GDI via win32ui
  - **Linux**: XGetImage via Xlib

### 2. Camada de Compatibilidade

Para Linux, são fornecidas classes de compatibilidade que emulam a API do pywin32:

- `Win32ConCompat`: Constantes (WM_*, VK_*, etc.)
- `Win32ApiCompat`: Funções utilitárias
- `Win32GuiCompat`: Funções de janela

Isso permite que o código existente funcione sem modificações:

```python
# Funciona tanto no Windows quanto no Linux
import win32gui
hwnd = win32gui.FindWindow(None, "Window Title")
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, 1, lparam)
```

## Dependências

### Windows
- **pywin32**: API nativa do Windows
- **ctypes**: Acesso direto ao kernel32

### Linux
- **python-xlib**: Interface com X11
- **ctypes**: Acesso à libc para process_vm_readv
- **psutil**: Informações de processos

### Multiplataforma
- PyQt5, numpy, opencv-python, pytesseract, etc.

## Detecção de Plataforma

```python
from Platform.PlatformAbstraction import IS_WINDOWS, IS_LINUX

if IS_WINDOWS:
    # Código específico do Windows
    import win32api
else:
    # Usa versão compatível do Linux
    from Platform.PlatformAbstraction import win32api
```

## Limitações Conhecidas

### Linux
1. **Wayland**: Suporte limitado. Recomenda-se X11
2. **Permissões**: Requer configuração de ptrace ou execução como root
3. **Wine**: Processos Wine podem não funcionar diretamente
4. **Desempenho**: Captura de tela pode ser mais lenta que no Windows

### Windows
1. **Privilégios**: Requer privilégios de depuração para alguns processos
2. **UAC**: Pode precisar de elevação de privilégios

## Fluxo de Execução

1. **StartBot.py** detecta a plataforma e configura Tesseract
2. **SelectTibiaTab** enumera processos usando `window_api`
3. **Addresses.py** abre o processo usando `memory_api`
4. **Threads** usam:
   - `memory_api` para ler estado do jogo
   - `input_api` para simular entrada
   - `screen_api` para OCR e detecção de imagens

## Adicionando Suporte a Nova Plataforma

Para adicionar macOS ou outra plataforma:

1. Adicione detecção em `PlatformAbstraction.py`:
   ```python
   IS_MACOS = PLATFORM == 'Darwin'
   ```

2. Implemente as APIs:
   - `MemoryAPI.read_process_memory()` usando API nativa
   - `WindowAPI` usando Cocoa/AppKit
   - `InputAPI` usando CGEvent
   - `ScreenCaptureAPI` usando CGWindowListCreateImage

3. Atualize `requirements.txt`:
   ```
   pyobjc-framework-Cocoa; sys_platform == 'darwin'
   ```

## Testes

### Windows
```bash
python -m pytest tests/ --platform=windows
```

### Linux
```bash
python3 -m pytest tests/ --platform=linux
```

## Contribuindo

Ao contribuir código multi-plataforma:

1. **Sempre teste em ambas as plataformas**
2. Use a camada de abstração, não APIs nativas diretamente
3. Documente comportamentos específicos de plataforma
4. Use `IS_WINDOWS`/`IS_LINUX` para lógica condicional mínima
5. Mantenha a paridade de funcionalidades entre plataformas

## Perguntas Frequentes

**Q: Por que não usar biblioteca multi-plataforma existente?**  
A: A funcionalidade específica (leitura de memória de processos, simulação de entrada em janelas específicas) requer APIs nativas. Bibliotecas genéricas não fornecem controle granular necessário.

**Q: O bot funciona no Wayland?**  
A: Parcialmente. Recomenda-se usar X11 para melhor compatibilidade.

**Q: Como debugar problemas específicos de plataforma?**  
A: Use logs detalhados e variável `IS_WINDOWS`/`IS_LINUX` para ativar debug específico.

**Q: Posso usar Wine no Linux?**  
A: Teoricamente sim, mas pode requerer configurações adicionais. Não é oficialmente suportado.

## Recursos Adicionais

- [PyQt5 Documentation](https://doc.qt.io/qtforpython/)
- [python-xlib Documentation](https://python-xlib.github.io/)
- [pywin32 Documentation](https://github.com/mhammond/pywin32)
- [Linux process_vm_readv](https://man7.org/linux/man-pages/man2/process_vm_readv.2.html)
