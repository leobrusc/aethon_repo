import argparse, json
from model_selection import run_phase2
def main():
    parser=argparse.ArgumentParser(description="Leakage-free lightweight detector selection and frozen evaluation")
    parser.add_argument("--output-root",default="results/revision/model_selection"); parser.add_argument("--seed",type=int,default=42)
    args=parser.parse_args(); print(json.dumps(run_phase2(args.output_root,args.seed),indent=2,default=str))
if __name__=="__main__": main()
