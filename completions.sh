_tbot()
{
    local cur prev words
    _init_completion || return

    # Collect testcase path arguments
    local index=0
    local path_args=()
    local curdir="$PWD"
    local workdir="${curdir}"
    while [[ $index -lt ${#words[@]} ]]; do
        local current_word="${words[$index]}"

        if [[ "$current_word" == @(-T|-t) ]]; then
            local index=$((index + 1))
            [[ "${words[$index]}" == "=" ]] && index=$((index + 1))
            local path="${words[$index]}"
            __expand_tilde_by_ref path
            path_args+=("$current_word" "$path")
        elif [[ "$current_word" == @* ]]; then
            path_args=("${path_args[@]}" "${current_word}")
        elif [[ "$current_word" == -C ]]; then
            local index=$((index + 1))
            [[ "${words[$index]}" == "=" ]] && index=$((index + 1))
            local path="${words[$index]}"
            __expand_tilde_by_ref path
            path_args+=("$current_word" "$path")
            workdir="$path"
        fi

        local index=$((index + 1))
    done

    if [[ "$prev" == -C ]]; then
        _filedir -d
        return
    fi

    if [[ "$prev" == -T ]]; then
        cd "${workdir}" && _filedir -d
        cd "${curdir}"
        return
    fi

    if [[ "$prev" == @(-t|-b|-l|--board|--lab) ]]; then
        cd "${workdir}" && _filedir py
        cd "${curdir}"
        # Remove __pycache__ for convenience
        COMPREPLY=("${COMPREPLY[@]/*__pycache__*/}")
        return
    fi

    if [[ "$cur" == \@* ]]; then
        cur="${cur:1}"
        _filedir

        # If the completion is a directory, append a / and prevent a space
        # being added.
        for i in "${!COMPREPLY[@]}"; do
            if [[ -d "${COMPREPLY[$i]}" ]]; then
                COMPREPLY[$i]+=/
                compopt -o nospace
            fi
        done

        COMPREPLY=("${COMPREPLY[@]/#/@}")
        return
    fi

    if [[ "$prev" == "--log" ]]; then
        cd "${workdir}" && _filedir
        cd "${curdir}"
        return
    fi

    if [[ "$prev" == @(-f) ]]; then
        COMPREPLY=()
        return
    fi

    if [[ "$cur" == -* ]]; then
        mapfile -t COMPREPLY < <(compgen -W '-h -b -l -T -t -f -v -q -s -i -C -p
            --help
            --board
            --lab
            --log
            --log-auto
            --version
            --list-testcases
            --list-files
            --list-flags
            --show
            --interactive
        ' -- "$cur")
    else
        # Collecting testcases can be really slow, so we cache them for
        # a small amount of time (5 seconds)
        local cache_age=$(($(date +%s) - ${__tbot_testcase_cache_time:-0}))
        if [[ -z $__tbot_testcase_cache || $cache_age -gt 5 ]]; then
            __tbot_testcase_cache=$(tbot --list-testcases "${path_args[@]}" 2>/dev/null | grep -v "selftest_")
            __tbot_testcase_cache_time=$(date +%s)
        fi
        mapfile -t COMPREPLY < <(compgen -W "$__tbot_testcase_cache" -- "$cur")
    fi
} &&
complete -F _tbot tbot

_newbot()
{
    local cur prev words
    _init_completion || return

    local index=0
    local path_args=()
    local curdir="$PWD"
    local workdir="${curdir}"
    while [[ $index -lt ${#words[@]} ]]; do
        local current_word="${words[$index]}"

        if [[ "$current_word" == -C ]]; then
            local index=$((index + 1))
            [[ "${words[$index]}" == "=" ]] && index=$((index + 1))
            local path="${words[$index]}"
            __expand_tilde_by_ref path
            path_args+=("$current_word" "$path")
            workdir="$path"
        fi

        local index=$((index + 1))
    done

    if [[ "$prev" == @(-b|-l|--board|--lab|-c|--config) ]]; then
        compopt -o nospace
        mapfile -t COMPREPLY < <(newbot -C "${workdir}" --complete-module "$cur")
        return
    fi

    if [[ "$prev" == -C ]]; then
        _filedir -d
        return
    fi

    if [[ "$cur" == -* ]]; then
        mapfile -t COMPREPLY < <(compgen -W '-h -C -c -f -v -q
            --help
            --config
            --version
        ' -- "$cur")
        return
    fi

    if [[ "$cur" == \@* ]]; then
        cur="${cur:1}"
        _filedir

        # If the completion is a directory, append a / and prevent a space
        # being added.
        for i in "${!COMPREPLY[@]}"; do
            if [[ -d "${COMPREPLY[$i]}" ]]; then
                COMPREPLY[$i]+=/
                compopt -o nospace
            fi
        done

        COMPREPLY=("${COMPREPLY[@]/#/@}")
        return
    fi

    compopt -o nospace
    mapfile -t COMPREPLY < <(newbot -C "${workdir}" --complete-testcase "$cur")
} &&
complete -F _newbot newbot
