module Internationalization.Suspicion exposing (..)

import Internationalization.Types exposing (TranslationSet)


mealPriceOutlier : TranslationSet
mealPriceOutlier =
    TranslationSet
        "Meal price is an outlier"
        "Preço de refeição muito incomum"


overMonthlySubquoteLimit : TranslationSet
overMonthlySubquoteLimit =
    TranslationSet
        "Expenses over the (sub)quota limit"
        "Extrapolou limita da (sub)quota"


suspiciousTraveledSpeedDay : TranslationSet
suspiciousTraveledSpeedDay =
    TranslationSet
        "Many expenses in different cities at the same day"
        "Muitas despesas em diferentes cidades no mesmo dia"


invalidCpfCnpj : TranslationSet
invalidCpfCnpj =
    TranslationSet
        "Invalid CNPJ or CPF"
        "CPF ou CNPJ inválidos"


electionExpenses : TranslationSet
electionExpenses =
    TranslationSet
        "Expense in electoral campaign"
        "Gasto com campanha eleitoral"


irregularCompany : TranslationSet
irregularCompany =
    TranslationSet
        "Irregular company"
        "CNPJ irregular"
