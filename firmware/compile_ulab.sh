#!/bin/bash

# Interrompe o script imediatamente se qualquer comando falhar
set -e

# Configurações de caminhos e versões corrigidas
BASE_DIR="$HOME/Projects/ulab_build"
MP_VERSION="v1.24.1"
IDF_VERSION="v5.2.3"
BOARD_NAME="ESP32_GENERIC_S3"
BOARD_VAR="SPIRAM_OCT"

echo "===================================================="
echo " 1. INSTALANDO DEPENDÊNCIAS DO SISTEMA (SUDO)"
echo "===================================================="
sudo apt-get update && sudo apt-get install -y \
  git wget make libncurses-dev flex bison gperf \
  python3 python3-pip python3-venv cmake ninja-build ccache

echo "===================================================="
echo " 2. CRIANDO E CONFIGURANDO DIRETÓRIOS"
echo "===================================================="
mkdir -p "$BASE_DIR"
cd "$BASE_DIR"

echo "--> Clonando repositório ulab..."
if [ ! -d "ulab" ]; then
    git clone https://github.com/v923z/micropython-ulab.git ulab
else
    echo "ulab já existe. Pulando clone."
fi

echo "--> Clonando repositório MicroPython..."
if [ ! -d "micropython" ]; then
    git clone https://github.com/micropython/micropython.git
fi

echo "--> Configurando MicroPython na versão estável correta ($MP_VERSION)..."
cd micropython
git fetch origin
git switch --detach "$MP_VERSION"
git submodule update --init --recursive
cd ..

echo "===================================================="
echo " 3. INSTALANDO E CONFIGURANDO ESP-IDF ($IDF_VERSION)"
echo "===================================================="
if [ ! -d "esp-idf" ]; then
    echo "--> Clonando ESP-IDF..."
    git clone -b "$IDF_VERSION" --recursive https://github.com/espressif/esp-idf.git
    cd esp-idf
    ./install.sh esp32s3
    cd ..
else
    echo "ESP-IDF já existe. Pulando clone e instalação."
fi

# Carrega as variáveis de ambiente do ESP-IDF no terminal atual
echo "--> Ativando ambiente do ESP-IDF..."
source esp-idf/export.sh

echo "===================================================="
echo " 4. COMPILANDO O MICROPYTHON CROSS-COMPILER (mpy-cross)"
echo "===================================================="
cd micropython
make -C mpy-cross
cd ..

echo "===================================================="
echo " 5. COMPILANDO FIRMWARE FINAL (ESP32-S3 + PSRAM + ULAB)"
echo "===================================================="
cd micropython/ports/esp32

# Limpa resíduos de compilações anteriores para evitar erros de cache
echo "--> Limpando cache antigo..."
rm -rf "build-${BOARD_NAME}-${BOARD_VAR}"

echo "--> Executando compilação via CMake/Ninja..."
make BOARD="$BOARD_NAME" BOARD_VARIANT="$BOARD_VAR" USER_C_MODULES="$BASE_DIR/ulab/code/micropython.cmake" all

echo "===================================================="
echo "  PROCESSO CONCLUÍDO COM SUCESSO!"
echo " Seu arquivo de firmware funcional está em:"
echo " $BASE_DIR/micropython/ports/esp32/build-${BOARD_NAME}-${BOARD_VAR}/firmware.bin"
echo "===================================================="
