module Format.Number exposing (formatNumber)

import String


addThousandSeparator : String -> String -> String
addThousandSeparator separator num =
    let
        parts : List String
        parts =
            String.split separator num

        firstPart : String
        firstPart =
            List.head parts |> Maybe.withDefault ""

        remainingParts : List String
        remainingParts =
            List.tail parts |> Maybe.withDefault []

        firstParts : List String
        firstParts =
            if String.length firstPart > 3 then
                let
                    newFirstPart : String
                    newFirstPart =
                        String.dropRight 3 firstPart
                in
                    [ addThousandSeparator separator newFirstPart
                    , String.right 3 firstPart
                    ]
            else
                [ firstPart ]
    in
        String.join separator <|
            List.concat
                [ firstParts
                , remainingParts
                ]


formatNumber : Int -> String -> String -> Float -> String
formatNumber decimals thousandSeparetor decimalSeparator num =
    if num == 0 then
        "0" ++ decimalSeparator ++ (String.repeat decimals "0")
    else
        let
            multiplier : Int
            multiplier =
                10 ^ decimals

            digits : String
            digits =
                num
                    |> (*) (toFloat multiplier)
                    |> round
                    |> toString

            intDigits : String
            intDigits =
                String.dropRight decimals digits

            decDigits : String
            decDigits =
                String.right decimals digits
        in
            String.concat
                [ addThousandSeparator thousandSeparetor intDigits
                , decimalSeparator
                , decDigits
                ]
