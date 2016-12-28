module Format.Date.I18n.I_pt_br exposing (..)

{-| Brazilian Portuguese values for day and month names.

@docs dayShort
@docs dayName
@docs monthShort
@docs monthName
@docs dayOfMonthWithSuffix

-}

import Date exposing (Day(..), Month(..))
import String exposing (padLeft)


{-| Day short name.
-}
dayShort : Day -> String
dayShort day =
    case day of
        Mon ->
            "Seg"

        Tue ->
            "Ter"

        Wed ->
            "Qua"

        Thu ->
            "Qui"

        Fri ->
            "Sex"

        Sat ->
            "Sáb"

        Sun ->
            "Dom"


{-| Day full name.
-}
dayName : Day -> String
dayName day =
    case day of
        Mon ->
            "Segunda-feira"

        Tue ->
            "Terça-feira"

        Wed ->
            "Quarta-feira"

        Thu ->
            "Quinta-feira"

        Fri ->
            "Sexta-feira"

        Sat ->
            "Sábado"

        Sun ->
            "Domingo"


{-| Month short name.
-}
monthShort : Month -> String
monthShort month =
    case month of
        Jan ->
            "Jan"

        Feb ->
            "Fev"

        Mar ->
            "Mar"

        Apr ->
            "Abr"

        May ->
            "Mai"

        Jun ->
            "Jun"

        Jul ->
            "Jul"

        Aug ->
            "Ago"

        Sep ->
            "Set"

        Oct ->
            "Out"

        Nov ->
            "Nov"

        Dec ->
            "Dez"


{-| Month full name.
-}
monthName : Month -> String
monthName month =
    case month of
        Jan ->
            "Janeiro"

        Feb ->
            "Fevereiro"

        Mar ->
            "Março"

        Apr ->
            "Abril"

        May ->
            "Maio"

        Jun ->
            "Junho"

        Jul ->
            "Julho"

        Aug ->
            "Agosto"

        Sep ->
            "Setembro"

        Oct ->
            "Outubro"

        Nov ->
            "Novembro"

        Dec ->
            "Dezembro"


{-| Returns a common Brazilian Portuguse idiom for days of month. Pad indicates
space pad the day of month value so single digit outputs have space padding to
make them same length as double digit days of month.
-}
dayOfMonthWithSuffix : Bool -> Int -> String
dayOfMonthWithSuffix pad day =
    let
        value =
            case day of
                1 ->
                    "1º"

                _ ->
                    toString day
    in
        if pad then
            padLeft 4 ' ' value
        else
            value
