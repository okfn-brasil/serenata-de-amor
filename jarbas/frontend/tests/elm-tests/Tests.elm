module Tests exposing (all)

import Test exposing (..)
import Expect
import Documents.Update
import Format.Number


all : Test
all =
    describe "Test suite"
        [ pagination
        , filters
        , format
        ]


pagination : Test
pagination =
    describe "Documents pagination"
        [ test "Documents.totalPages" <|
            \() ->
                Expect.equal (Documents.Update.totalPages 20) 3
        ]


filters : Test
filters =
    describe "Inut filters"
        [ test "Documents.onlyDigits" <|
            \() ->
                Expect.equal (Documents.Update.onlyDigits "12a3") "123"
        ]


format : Test
format =
    describe "Format number"
        [ test "Format.Number.formatNumber 12345678.90123" <|
            \() ->
                Expect.equal (Format.Number.formatNumber 2 "." "," 12345678.90123) "12.345.678,90"
        , test "Format.Number.formatNumber 3.999" <|
            \() ->
                Expect.equal (Format.Number.formatNumber 2 "." "," 3.456) "3,46"
        , test "Format.Number.formatNumber 1" <|
            \() ->
                Expect.equal (Format.Number.formatNumber 2 "." "," 1) "1,00"
        , test "Format.Number.formatNumber 0.0" <|
            \() ->
                Expect.equal (Format.Number.formatNumber 2 "." "," 0.0) "0,00"
        ]
