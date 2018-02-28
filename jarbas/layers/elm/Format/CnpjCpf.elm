module Format.CnpjCpf exposing (formatCnpj, formatCnpjCpf, formatCpf)

import String


{-| Format a CPF number:

    formatCpf "12345678901" --> "123.456.789-01"

-}
formatCpf : String -> String
formatCpf cpf =
    let
        part1 =
            String.slice 0 3 cpf

        part2 =
            String.slice 3 6 cpf

        part3 =
            String.slice 6 9 cpf

        part4 =
            String.slice 9 11 cpf
    in
        String.concat
            [ part1
            , "."
            , part2
            , "."
            , part3
            , "-"
            , part4
            ]


{-| Format a CNPJ number:

    formatCnpj "12345678901234" --> "12.345.678/9012-34"

-}
formatCnpj : String -> String
formatCnpj cnpj =
    let
        part1 =
            String.slice 0 2 cnpj

        part2 =
            String.slice 2 5 cnpj

        part3 =
            String.slice 5 8 cnpj

        part4 =
            String.slice 8 12 cnpj

        part5 =
            String.slice 12 14 cnpj
    in
        String.concat
            [ part1
            , "."
            , part2
            , "."
            , part3
            , "/"
            , part4
            , "-"
            , part5
            ]


{-| Format a CNPJ or CPF number:

    formatCnpjCpf "12345678901" --> "123.456.789-01"

    formatCnpjCpf "12345678901234" --> "12.345.678/9012-34"

    formatCnpjCpf "42" --> "42"

-}
formatCnpjCpf : String -> String
formatCnpjCpf value =
    case String.length value of
        11 ->
            formatCpf value

        14 ->
            formatCnpj value

        _ ->
            value
