module Format.Date.Config.Config_pt_br exposing (..)

{-| This is the Brazilian Portuguese config for formatting dates.

@docs config

-}

import Date
import Date.Extra.Config as Config
import Format.Date.I18n.I_pt_br as Portuguese


{-| Config for pt-br.
-}
config : Config.Config
config =
    { i18n =
        { dayShort = Portuguese.dayShort
        , dayName = Portuguese.dayName
        , monthShort = Portuguese.monthShort
        , monthName = Portuguese.monthName
        , dayOfMonthWithSuffix = Portuguese.dayOfMonthWithSuffix
        }
    , format =
        { date = "%d/%m/%Y"
        , longDate = "%A, %-d de %B de %Y"
        , time = "%H:%M"
        , longTime = "%H:%M:%S"
        , dateTime = "%d/%m/%Y %H:%M"
        , firstDayOfWeek = Date.Sun
        }
    }
