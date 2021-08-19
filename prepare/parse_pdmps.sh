#! /bin/bash

if [ $# -lt 2 ]; then
    echo "Usage: parse_pdmps.sh directory num_clusters"
    echo "Assumes directory has zero or more of:"
    echo "    directory/edges<num_clusters>/"
    echo "    directory/hosts<num_clusters>/"
    echo "    directory/eval<num_clusters>/"
    exit 1
fi

shopt -s nullglob

if [[ -d "${1}/hosts${2}" && ! -f ${1}/hosts${2}/hosts.raw ]]; then
    echo "Parsing pdmps of hosts..."

    for filename in ${1}/hosts${2}/*.pdmp; do
        basename=${filename%.pdmp}
        IFS='_'; toks=($basename); unset IFS;
        TOR=${toks[${#toks[@]}-2]}
        SVR=${toks[${#toks[@]}-1]}
        IFS='.'; toks=($SVR); unset IFS;
        SVR=${toks[0]}
        sed -e "s/\$/ tor $TOR svr $SVR/" "$basename.pdmp" > $basename.tmp
        sed -e "s/Packet EthernetIIFrame '.*': \[//" "$basename.tmp" > $basename.dump
        rm $basename.tmp
    done

    echo "Merging host tcpdumps..."
    sort -s -m -g -k1,1 -o "${1}/hosts${2}/hosts.raw" ${1}/hosts${2}/*.dump
fi

if [[ -d "${1}/edges${2}" && ! -f ${1}/edges${2}/edges.raw ]]; then
    echo "Parsing pdmps of edges..."

    for filename in ${1}/edges${2}/*.pdmp; do
        basename=${filename%.pdmp}
        IFS='_'; toks=($basename); unset IFS;
        AGG=${toks[${#toks[@]}-2]}
        ETH=${toks[${#toks[@]}-1]}
        INTF=${ETH:3:1}
        sed -e "s/\$/ agg $AGG interface $INTF/" "$basename.pdmp" > $basename.tmp
        sed -e "s/Packet EthernetIIFrame '.*': \[//" "$basename.tmp" > $basename.dump
        rm $basename.tmp
    done

    echo "Merging edge tcpdumps..."
    sort -s -m -g -k1,1 -o "${1}/edges${2}/edges.raw" ${1}/edges${2}/*.dump
fi

if [[ -d "${1}/eval${2}" && ! -f ${1}/eval${2}/eval.raw ]]; then
    echo "Parsing evaluation pdmps..."

    for filename in ${1}/eval${2}/*.pdmp; do
        basename=${filename%.pdmp}
        IFS='_'; toks=($basename); unset IFS;
        TOR=${toks[${#toks[@]}-2]}
        SVR=${toks[${#toks[@]}-1]}
        IFS='.'; toks=($SVR); unset IFS;
        SVR=${toks[0]}
        sed -e "s/\$/ tor $TOR svr $SVR/" "$basename.pdmp" > $basename.tmp
        sed -e "s/Packet EthernetIIFrame '.*': \[//" "$basename.tmp" > $basename.dump
        rm $basename.tmp
    done

    echo "Merging eval tcpdumps..."
    sort -s -m -g -k1,1 -o "${1}/eval${2}/eval.raw" ${1}/eval${2}/*.dump
fi
