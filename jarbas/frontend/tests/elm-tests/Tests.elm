module Tests exposing (..)

import Test exposing (..)
import Expect
import String
import Documents exposing (..)


all : Test
all =
    describe "Documents"
        [ test "Documents.totalPages" <|
            \() ->
                Expect.equal (Documents.totalPages 20) 3
        , test "Documents.onlyDigits" <|
            \() ->
                Expect.equal (Documents.onlyDigits "12a3") "123"
        ]
