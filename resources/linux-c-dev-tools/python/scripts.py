from pathlib import Path


def command_outs_concat(args):
    output = Path(args.output)
    outs = Path('outs')
    index = 0

    with output.open('w') as fout:
        fout.write('[')
        for file in outs.glob('*'):
            with file.open('r') as fin:
                for line in fin:
                    if index == 0:
                        fout.write('\n  ')
                    else:
                        fout.write(',\n  ')
                    fout.write(line.strip())
                    index += 1
        fout.write('\n]')


def command_outs_remove(args):
    outs = Path('outs')
    for file in outs.glob('*'):
        file.unlink()


def get_parse_args():
    def is_json(path):
        if path.endswith('.json'):
            return path
        else:
            raise argparse.ArgumentTypeError('Expect a valid json file path')

    import argparse
    parser = argparse.ArgumentParser(description='Helpers')
    subparsers = parser.add_subparsers(dest='command')

    outs_concat_cmd = subparsers.add_parser(
        'outs-concat', help='Concatenate all output files')
    outs_concat_cmd.add_argument('-o', '--output', type=is_json, required=True)

    subparsers.add_parser(
        'outs-remove', help='Remove all output files')

    return parser


if __name__ == '__main__':
    parser = get_parse_args()
    args = parser.parse_args()
    command = f'command_{args.command.replace("-", "_")}'
    if command in globals():
        globals()[command](args)
    else:
        parser.print_help()
        exit(1)
