"""One entry point: python run_all.py"""

import stage1
import stage2
import stage3
import stage4
import stage4_hybrid


def main():
    stage1.main()
    stage2.main()
    stage3.main()
    stage4.main()
    stage4_hybrid.main()


if __name__ == "__main__":
    main()
