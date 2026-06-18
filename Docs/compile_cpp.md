# Criando Módulos Nativos em C++ para MicroPython (.mpy)

Este guia prático demonstra como escrever algoritmos de alta performance em **C++**, compilá-los separadamente como um arquivo `.mpy` (Módulo Nativo Dinâmico) e importá-los diretamente no **MicroPython** sem a necessidade de recompilar todo o firmware da placa.

---

## 🚀 Como Funciona?
O MicroPython possui uma API em tempo de execução chamada `py/dynruntime.h`. Ela permite carregar binários pré-compilados diretamente na memória RAM do microcontrolador. 

Como a ABI interna do MicroPython espera uma estrutura em **C**, qualquer código **C++** precisa ter suas funções de interface envelopadas dentro de blocos `extern "C"`.

---

## 📄 1. Código Fonte (`meumodulo.cpp`)

Crie o arquivo `meumodulo.cpp`. Ele contém sua classe em C++ e as funções "wrapper" que fazem a ponte de comunicação com o Python.

```cpp
extern "C" {
    #include "py/dynruntime.h" // Cabeçalho obrigatório do MicroPython
}

// ==========================================
// 1. SUA LÓGICA PURAMENTE EM C++
// ==========================================
class Calculadora {
public:
    int somar(int a, int b) {
        return a + b;
    }
};

// ==========================================
// 2. WRAPPER "C" PARA INTERFACE COM PYTHON
// ==========================================
extern "C" {

    // Função que será chamada de dentro do MicroPython
    mp_obj_t meumodulo_somar(mp_obj_t a_obj, mp_obj_t b_obj) {
        // Extrai e converte inteiros vindos do MicroPython
        mp_int_t a = mp_obj_get_int(a_obj);
        mp_int_t b = mp_obj_get_int(b_obj);

        // Instancia e executa sua classe C++ normalmente
        Calculadora calc;
        int resultado = calc.somar(a, b);

        // Retorna o resultado convertido de volta para objeto MicroPython
        return mp_obj_new_int(resultado);
    }

    // ==========================================
    // 3. FUNÇÃO DE INICIALIZAÇÃO (Chamada no 'import')
    // ==========================================
    mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args) {
        // Define o nome do escopo do módulo
        mp_designate_module(MP_OBJ_NEW_QSTR(MP_QSTR_meumodulo));

        // Registra a função 'somar' no escopo global do módulo esperando 2 argumentos
        mp_store_global(MP_QSTR_somar, mp_make_function_n(2, (mp_fun_ptr_t)meumodulo_somar));

        return mp_const_none;
    }
}
```

---

## 🛠️ 2. O arquivo de compilação (`Makefile`)

O MicroPython utiliza um sistema baseado em Makefiles para gerenciar as *toolchains* de compilação cruzada. Crie um arquivo chamado `Makefile`:

```makefile
# Nome do arquivo final gerado (meumodulo.mpy)
MOD = meumodulo

# Arquivo fonte do seu projeto
SRC = meumodulo.cpp

# Arquitetura do seu chip de destino:
# - xtensawin  -> ESP32 padrão
# - xtensa     -> ESP8266
# - armv6m     -> Raspberry Pi Pico (RP2040 / RP2350)
# - armv7m     -> STM32 padrão
# - x86 / x64  -> MicroPython versão Unix/PC
ARCH = xtensawin

# Caminho absoluto ou relativo para a raiz do repositório clonado do MicroPython
MPY_DIR = ../micropython

# Inclui as regras oficiais do MicroPython para módulos nativos
include $(MPY_DIR)/py/dynruntime.mk
```

---

## 📦 3. Compilando e Gerando o arquivo `.mpy`

### Pré-requisitos na Máquina de Desenvolvimento (PC):
1. Ter o repositório oficial do MicroPython baixado localmente (`git clone https://github.com`).
2. Ter instalado o compilador correspondente à arquitetura do chip (ex: `arm-none-eabi-g++` para Pi Pico ou `xtensa-esp32-elf-g++` para ESP32).

### Comando de Compilação:
Abra o terminal na pasta dos arquivos criados e digite:
```bash
make
```
Isso acionará o script interno `mpy_ld.py` do MicroPython, que compilará o C++ e gerará o arquivo final **`meumodulo.mpy`**.

---

## 🐍 4. Como usar no MicroPython

1. Envie o arquivo `meumodulo.mpy` gerado para a memória flash da sua placa (usando Thonny IDE, `ampy` ou `mpremote`).
2. No seu script Python (ex: `main.py`), basta realizar o import direto:

```python
import meumodulo

# Executa a função processada de forma nativa em C++ pelo hardware
resultado = meumodulo.somar(15, 30)

print("Resultado vindo do C++:", resultado)
# Saída esperada: Resultado vindo do C++: 45
```

---

## ⚠️ Restrições Cruciais (Estude com atenção!)

* **Gerenciamento de Memória:** O MicroPython roda seu próprio *Garbage Collector* (GC). Se o seu código C++ precisar alocar memória dinâmica, use as macros do MicroPython como `m_malloc()` e `m_free()` em vez de `new`/`delete` ou `malloc()` tradicional, para evitar corromper o Heap do sistema.
* **Evite o Standard Template Library (STL):** Incluir recursos pesados do C++ como `std::cout`, `std::string` ou `<iostream>` aumentará drasticamente o tamanho do binário. Como microcontroladores possuem pouca RAM, prefira tipos primitivos e estruturas leves.
* **Acesso ao SDK Nativo limitado:** Módulos `.mpy` isolados não conseguem acessar facilmente funções profundas do fabricante do chip (como APIs do ESP-IDF da Expressif), a menos que você faça o mapeamento manual de ponteiros de funções. Eles são ideais para processamento de dados puros, criptografia ou lógica matemática.
