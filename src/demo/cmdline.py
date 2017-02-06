"""
This is temporarily here (and in this package) for demonstration purposes.
"""

import argparse
from mashingpumpkins import _murmurhash3_mash
from mashingpumpkins.minhashsketch import MinSketch
from mashingpumpkins.parallel import Sketch
from mashingpumpkins.sequence import chunkpos_iter
import mashingpumpkins.sourmash
from array import array
import multiprocessing
import sourmash_lib.signature
from functools import reduce
import time
import sys
import gzip
import pickle

FORMAT_SOURMASH_JSON = 'sourmash-json'
FORMAT_MASHINGPUMPKINS_PICKLE = 'mashingpumpkins-pickle'

def reads_in_chunks(reader, chunksize, nsize, metrics):
    chunk = list()
    currentsize = 0
    progress_step = 50000
    for n, (header, sequence, quality) in enumerate(reader, 1):
        if n % progress_step == 0:
            print('\r    %i entries' % n, end='', flush=True)
        lseq = len(sequence)
        if lseq > chunksize:
            for beg, end in chunkpos_iter(nsize, lseq, chunksize):
                metrics[1] += lseq
                yield (sequence[beg:end],)
            continue
        else:
            chunk.append(sequence)
            currentsize += len(sequence)
            if currentsize >= chunksize:
                metrics[1] += currentsize
                yield chunk
                chunk = list()
                currentsize = 0
    metrics[0] = n
    if currentsize >= 0:
        metrics[1] += currentsize
        yield chunk
    print('\r    %i records' % (n+1), end='', flush=True)

def prettytime(secs):
    mins = secs // 60
    secs = secs % 60 + (secs - int(secs))
    if mins == 0:
        return '%.2fs' % secs
    hours = mins // 60
    if hours == 0:
        return '%im%is' % (mins, secs)
    mins = mins % 60
    return '%ih%im%is' % (hours, mins, secs)

def make_argparser():
    parser = argparse.ArgumentParser('Technological demo: generating MinHash sketch somewhat faster than other options.')
    parser.add_argument('--format',
                        choices = ('FASTQ', 'FASTA'),
                        default = 'FASTQ',
                        help = 'File format (default: %(default)s')
    parser.add_argument('--maxsize',
                        type = int,
                        default = 1000,
                        help = 'Maximum number of values in the sketch (default: %(default)i)')
    parser.add_argument('--ksize',
                        default = 31,
                        type = int,
                        help = 'k value in "k-mer" (default: %(default)i)')
    parser.add_argument('--aggregate',
                        action = 'store_true',
                        help = 'Produces one MinHash sketch for the all files. '
                        'Whenever this flag is set the parameter --aggregate-prefix must also be specified.')
    parser.add_argument('--aggregate-prefix',
                        help = 'File/path prefix to save the aggregate signature into. '
                        'The suffix \'.sig.json\' will be added to this prefix '
                        'This is only needed when the flag --aggregate is set.')
    parser.add_argument('--ncpu',
                        type = int,
                        default = 2,
                        help = 'Number of cores to use. Optimal results may require adjusting --chunksize (default: %(default)i)')
    parser.add_argument('--output-format',
                        default = FORMAT_SOURMASH_JSON,
                        choices = (FORMAT_SOURMASH_JSON, FORMAT_MASHINGPUMPKINS_PICKLE),
                        help = 'Output format for the sketch (default: %(default)s).')
    parser.add_argument('--parser',
                        default = 'ngs_plumbing',
                        choices = ('ngs_plumbing', 'fastqandfurious'),
                        help = 'Parser used (default: %(default)s).')
    parser.add_argument('--chunksize',
                        default = int(5E6),
                        type = int,
                        help = 'Chunk size for parallelization. '
                        'Benchmarks suggest that this number should be increased '
                        'for larger values of --ksize than the default, '
                        'e.g., 1E7 for ksize=10000, 5E7 for ksize=50000, ... '
                        '(default: %(default)i)')
    parser.add_argument('--fbufsize',
                         type = int,
                         default = 100000,
                         help = 'Buffer size when reading an input file (default: %(default)i)')
    parser.add_argument('filename',
                        nargs = '*',
                        help = 'Filename (FASTA or FASTQ, and optionally gzip-compressed)')
    return parser

if __name__ == '__main__':

    parser = make_argparser()
    args = parser.parse_args()

    if args.ncpu < 2:
        print('The minimal number of CPU/cores is 2.')
        sys.exit(1)
        
    if args.aggregate and args.aggregate_prefix is None:
        print('Whenever the flag --aggregate is set the parameter --aggregate-prefix must also be specified.')
        sys.exit(1)

    if args.output_format == FORMAT_SOURMASH_JSON:
        def save_func(sketches, fh_out):
            sourmash_lib.signature.save_signatures(sketches, fp=fh_out)

    if args.parser == 'ngs_plumbing':
        try:
            import ngs_plumbing.fasta
            import ngs_plumbing.fastq
        except ImportError as ie:
            print(ie)
            sys.exit(1)
        if args.format == 'FASTQ':
            parser = ngs_plumbing.fastq.read_fastq
        elif args.format == 'FASTA':
            parser = ngs_plumbing.fastq.read_fasta
    elif args.parser == 'fastqandfurious':
        try:
            from fastqandfurious import fastqandfurious, _fastqandfurious
        except ImportError as ie:
            print(ie)
            sys.exit(1)
        if args.format == 'FASTQ':
            parser = lambda fh: fastqandfurious.readfastq_iter(fh, 20000, _entrypos=_fastqandfurious.entrypos)        
        elif args.format == 'FASTA':
            print('Error: no FASTA parser with fastqandfurious')
            sys.exit(1)
    cls = MinSketch
    seed = 42
    hashfun = mashingpumpkins.sourmash.mash_hashfun

    if len(args.filename) == 0:
        print('Nothing to do, so nothing was done. Try --help.')
        sys.exit(0)
    elif not args.aggregate:
        # empty sketch (will be updated as we process files)
        total_mhs = cls(args.ksize, args.maxsize,
                        hashfun, seed)        
        
    for fn in args.filename:
        print('Processing %s ' % fn, end='', flush=True)

        metrics = [0, 0]
        with open(fn, mode='rb', buffering=args.fbufsize) as fh:
            if fn.endswith('.gz'):
                fh = gzip.open(fh)

            if args.format == 'FASTQ':
                reader = parser(fh)
                print('as a FASTQ file...', flush=True)
            elif args.format == 'FASTA':
                reader = parser(fh)
                print('as a FASTA file...', flush=True)
            else:
                print('*** Unknown format.')
                sys.exit(1)
            t0 = time.time()
            p = multiprocessing.Pool(args.ncpu-1, # one cpu will be used by this process (the parent)
                                     initializer=Sketch.initializer,
                                     initargs=(cls, args.ksize, args.maxsize,
                                               hashfun, seed))
            try:
                result = p.imap_unordered(Sketch.map_sequences,
                                          reads_in_chunks(reader, args.chunksize, args.ksize, metrics))
                mhs_mp = reduce(Sketch.reduce, result, cls(args.ksize, args.maxsize, hashfun, seed))
            finally:
                p.terminate()
        if args.aggregate:
            total_mhs.update(mhs_up)
        else:
            if args.output_format == FORMAT_SOURMASH_JSON:
                sms = mashingpumpkins.sourmash.to_sourmashsignature(mhs_mp)
                with open(fn + '.sig.json', 'w') as fh_out:
                    save_func([sms], fh_out)
            elif args.output_format == FORMAT_MASHINGPUMPKINS_PICKLE:
                with open(fn + '.sig.pkl', 'wb') as fh_out:
                    pickle.dump(mhs_mp, fh_out)
                
        t1 = time.time()
        print('\r    %i records in %s (%.2f MB/s)' % (metrics[0]+1, prettytime(t1-t0), metrics[1]/1E6/(t1-t0)))
    if args.aggregate:
        if args.output_format == FORMAT_SOURMASH_JSON:
            sms = mashingpumpkins.sourmash.to_sourmashsignature(total_mhs)
            with open(args.aggregate_prefix + '.sig.json', 'w') as fh_out:
                save_func([sms], fh_out)
        elif args.output_format == FORMAT_MASHINGPUMPKINS_PICKLE:
            with open(fn + '.sig.pkl', 'wb') as fh_out:
                pickle.dump(total_mhs, fh_out)

