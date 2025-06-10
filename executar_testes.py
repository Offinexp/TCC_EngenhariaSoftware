import sys
import subprocess
import json
import pandas as pd
import matplotlib.pyplot as plt
import os

errors = []

print("[1] Executando testes com benchmark e relatório JSON...")

result = subprocess.run([
    sys.executable, "-m", "pytest",
    "sistema_estoque/testes",
    "--benchmark-only",
    "--benchmark-save=execucao",
    "--json-report",
    "--json-report-file=resultado.json",
    "-v",
    "--capture=no"
])

if result.returncode != 0:
    errors.append("⚠️ Erro ao executar os testes. Verifique os logs acima.")

print("[2] Exportando benchmark para CSV...")

benchmark_file = os.path.join('.benchmarks', 'execucao.benchmarks')

if not os.path.exists(benchmark_file):
    errors.append(f"❌ Arquivo de benchmark não encontrado: {benchmark_file}")
else:
    try:
        with open(benchmark_file, encoding='utf-8') as f:
            benchmarks = json.load(f)

        df = pd.DataFrame(benchmarks)

        if 'stats' not in df.columns:
            errors.append("❌ Estrutura inesperada no arquivo de benchmark: coluna 'stats' não encontrada.")
        else:
            # Extrair mean e stddev de microssegundos para segundos
            df['mean'] = df['stats'].apply(lambda x: x['mean'] / 1_000_000)
            df['stddev'] = df['stats'].apply(lambda x: x['stddev'] / 1_000_000)

            df_csv = df[['name', 'mean', 'stddev']]
            df_csv.to_csv('benchmark.csv', index=False)
            print("✅ Benchmark exportado para benchmark.csv")
    except Exception as e:
        errors.append(f"❌ Erro ao processar benchmark: {e}")

print("[3] Analisando resultado.json...")

if not os.path.exists('resultado.json'):
    errors.append("❌ Arquivo resultado.json não encontrado. Verifique se os testes foram executados corretamente.")
else:
    try:
        with open('resultado.json', encoding='utf-8') as f:
            data = json.load(f)

        summary = data.get('summary', {})
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        skipped = summary.get('skipped', 0)

        print(f"\n🔢 Resultados Gerais:")
        print(f"✔️  Testes Passaram: {passed}")
        print(f"❌  Testes Falharam: {failed}")
        print(f"⏭️  Testes Pulados: {skipped}")
        print(f"📊  Total Executado: {total}")
        if total > 0:
            print(f"📉 Frequência relativa de falhas: {(failed / total * 100):.2f}%\n")
        else:
            print("⚠️ Nenhum teste executado.\n")
    except Exception as e:
        errors.append(f"❌ Erro ao processar resultado.json: {e}")

print("[4] Gerando gráfico a partir do benchmark...")

if not os.path.exists('benchmark.csv'):
    errors.append("❌ Arquivo benchmark.csv não encontrado. Verifique se o benchmark foi salvo corretamente.")
else:
    try:
        df = pd.read_csv('benchmark.csv')

        if {'name', 'mean', 'stddev'}.issubset(df.columns):
            df = df.set_index('name')

            # Ordena pelos testes mais lentos e pega top 10
            df_sorted = df.sort_values('mean', ascending=False).head(10)

            plt.figure(figsize=(12, 7))
            ax = df_sorted.plot(kind='bar', y=['mean', 'stddev'], title='Top 10 Testes por Tempo Médio (segundos)')
            ax.set_ylabel('Tempo (s)')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig('grafico_tempos.png')
            plt.show()

            print("\n✅ Análise finalizada com sucesso. Verifique o gráfico gerado: 'grafico_tempos.png'")
        else:
            errors.append("⚠️ As colunas esperadas ('name', 'mean', 'stddev') não foram encontradas no CSV.")
    except Exception as e:
        errors.append(f"❌ Erro ao gerar gráfico: {e}")

if errors:
    print("\n===== RESUMO DE ERROS E AVISOS =====")
    for e in errors:
        print(e)
else:
    print("\n✅ Processo concluído sem erros.")