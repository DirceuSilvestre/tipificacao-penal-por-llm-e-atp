import csv
import json
from pathlib import Path
from pathlib import Path
from typing import Union

def jsonl_para_csv_nativo(caminho_jsonl: str, caminho_csv: str) -> None:
    caminho_in = Path(caminho_jsonl)
    caminho_out = Path(caminho_csv)

    with caminho_in.open("r", encoding="utf-8") as f_in:
        # Lê a primeira linha para extrair as chaves do cabeçalho
        primeira_linha = f_in.readline()
        if not primeira_linha.strip():
            return

        primeiro_registro = json.loads(primeira_linha)
        cabecalho = list(primeiro_registro.keys())

        with caminho_out.open("w", encoding="utf-8", newline="") as f_out:
            escritor = csv.DictWriter(f_out, fieldnames=cabecalho, delimiter=";")
            escritor.writeheader()
            escritor.writerow(primeiro_registro)

            # Escreve o restante linha a linha (Streaming)
            for linha in f_in:
                if linha.strip():
                    escritor.writerow(json.loads(linha))


def converter_todos_jsonl_para_csv(
    diretorio_entrada: Union[str, Path], 
    diretorio_saida: Union[str, Path, None] = None
) -> list[Path]:
    """Varre um diretório por arquivos .jsonl e converte cada um para .csv.

    Args:
        diretorio_entrada: Pasta onde estão os arquivos .jsonl.
        diretorio_saida: Pasta onde os arquivos .csv serão salvos.
            Se None, salva na mesma pasta do arquivo de origem.

    Returns:
        Lista com os caminhos dos arquivos .csv criados.
    """
    pasta_in = Path(diretorio_entrada)
    pasta_out = Path(diretorio_saida) if diretorio_saida else pasta_in

    if not pasta_in.exists():
        raise FileNotFoundError(f"O diretório informado não existe: {pasta_in.resolve()}")

    pasta_out.mkdir(parents=True, exist_ok=True)
    arquivos_convertidos = []

    # Localiza todos os arquivos com extensão .jsonl na pasta
    for arquivo_jsonl in pasta_in.glob("*.jsonl"):
        # Define o nome do .csv mantendo o mesmo nome base do arquivo
        caminho_csv = pasta_out / f"{arquivo_jsonl.stem}.csv"
        
        # Chama a função nativa de conversão
        jsonl_para_csv_nativo(arquivo_jsonl, caminho_csv)

# Exemplo de uso:
# jsonl_para_csv_nativo("dados.jsonl", "saida.csv")

if __name__ == "__main__":
    # Converte todos os .jsonl de 'data/classified' e salva os .csv na mesma pasta
    # arquivos = converter_todos_jsonl_para_csv("data/organized")
    caminho_jsonl = "data/classified/resultados_classificados_modelo_2_dataset_curado.jsonl"
    caminho_csv = "data/classified/resultados_classificados_modelo_2_dataset_curado.csv"
    jsonl_para_csv_nativo(caminho_jsonl, caminho_csv)