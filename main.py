from services.reconciliation import ReconciliationEngine

def main():
    engine = ReconciliationEngine()

    # Full pipeline — read, process, analyze, write output
    engine.run(
        input_file="data/transactions.csv",
        output_dir="data/output",
    )

    # Print detailed analytics
    if engine.analytics:
        engine.analytics.print_report()

    # Demo: lazy mode (generator-based, low memory)
    print()
    print()
    engine_lazy = ReconciliationEngine()
    engine_lazy.run_lazy("data/transactions.csv")


if __name__ == "__main__":
    main()