#!/usr/bin/env bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT
set -e

# Adds copyright notice if missing and fix the year range if necessary

FILES=$(git ls-files '*.h' '*.c' '*.py' '*CMakeLists.txt' '*.sh' '*.cmake' | grep -v 'deps')

# we use GNU sed
SED=sed
if ! sed --version > /dev/null 2>&1; then
    # if this is not GNU sed, try gsed
    if gsed --version > /dev/null 2>&1; then
        SED=gsed
    else
        echo "This script requires GNU sed"
        exit 1
    fi
fi

COPYRIGHT_TEXT_CMAKE="\
\# Copyright (C) Huawei Technologies Co., Ltd. <RANGE>. All rights reserved.\n\
\# SPDX-License-Identifier: MIT\n\n"

COPYRIGHT_TEXT_C="\
/*\n\
 * Copyright (C) Huawei Technologies Co., Ltd. <RANGE>. All rights reserved.\n\
 * SPDX-License-Identifier: MIT\n\
 */\n"

COPYRIGHT_TEXT_PY="\
\# Copyright (C) Huawei Technologies Co., Ltd. <RANGE>. All rights reserved.\n\
\# SPDX-License-Identifier: MIT\n\n"

COPYRIGHT_TEXT_SH="\
\# Copyright (C) Huawei Technologies Co., Ltd. <RANGE>. All rights reserved.\n\
\# SPDX-License-Identifier: MIT\n\n"


fix_shebang() {
    # This function is AI generated
    file="$1"

    # Read the first line
    first_line=$(head -n 1 "$file")

    # If the first line already starts with #!, nothing to do
    if [[ "$first_line" =~ ^#! ]]; then
        return
    fi

    # Find the shebang line number (if any)
    shebang_line=$(grep -n '^#!' "$file" | cut -d: -f1 | head -n 1)

    # If no shebang exists, nothing to do
    if [[ -z "$shebang_line" ]]; then
        return
    fi

    # Extract the shebang
    shebang=$(sed -n "${shebang_line}p" "$file")

    # Remove the shebang from its original location
    tmp=$(mktemp)
    sed "${shebang_line}d" "$file" > "$tmp"

    # Prepend the shebang to the file
    {
        echo "$shebang"
        cat "$tmp"
    } > "$file"

    rm "$tmp"
}

for f in ${FILES}; do
    echo CHECK: ${f}

    fname=$(basename -- "${f}")
    ext="${fname##*.}"
    if [ "$ext" = "txt" ] || echo $fname | grep cmake > /dev/null; then
        COPYRIGHT_TEXT="$COPYRIGHT_TEXT_CMAKE"
    elif [ "$ext" = "py" ]; then
        COPYRIGHT_TEXT="$COPYRIGHT_TEXT_PY"
    elif [ "$ext" = "sh" ]; then
        COPYRIGHT_TEXT="$COPYRIGHT_TEXT_SH"
    else
        COPYRIGHT_TEXT="$COPYRIGHT_TEXT_C"
    fi

    # add copyright notice
    EXP_END=$(git log --follow --format=%ad --date=format:'%Y' $f | head -1)
    EXP_START=$(git log --follow --format=%ad --date=format:'%Y' $f | tail -1)

    if [[ "$EXP_START" == "$EXP_END" ]]; then
        REPLACEMENT="$EXP_START"
    else
        REPLACEMENT="$EXP_START-$EXP_END"
    fi

    # Update (if necessary) date of the first (top-most) copyright line
    # The echo empty is necessary for the case when there is no copyright
    # notice in the file
    COPYRIGHT=$(grep Copyright ${f} | head -n1 || true)

    if [ -z "$COPYRIGHT" ]; then
        NOTICE="${COPYRIGHT_TEXT/<RANGE>/$REPLACEMENT}"
        echo "Adding copyright notice to $f"
        $SED -i "1s;^;${NOTICE};" ${f}
    else
        REGEX="Copyright.* ([0-9]+)\-?([0-9]+)?"
        if [[ "$COPYRIGHT" =~ $REGEX ]]; then
            CUR_START="${BASH_REMATCH[1]}"
            CUR_END="${BASH_REMATCH[2]}"
            if [ -z "$CUR_END" ]; then
                ORIGINAL=$CUR_START
            else
                ORIGINAL="$CUR_START-$CUR_END"
            fi
        else
            echo "[ERROR] copyright without year in $f"
            exit 1
        fi

        if [[ $REPLACEMENT != $ORIGINAL ]]; then
            echo "Updating copyrights notice in ${f} ${ORIGINAL} ==> ${REPLACEMENT}"
            $SED -i 's|\(.*Copyright.*\) '${ORIGINAL}'|\1 '${REPLACEMENT}'|g' ${f}
        fi

        if [ "$ext" = "sh" ]; then
            fix_shebang "$f"
        fi
    fi

    # Ensure file has SDPX line after the *last* Copyright line
    if ! grep SPDX $f > /dev/null; then
        echo "Adding license to ${f}"
        PREFIX="$(echo "$COPYRIGHT" | sed 's/^\(.*\)Copyright.*$/a\\\n\1/')"
        LINE=$(grep -n Copyright ${f} | tail -1 | cut -d: -f1)
        $SED -i "${LINE}${PREFIX}SPDX-License-Identifier: MIT" ${f} | head -n 10
    fi
done
