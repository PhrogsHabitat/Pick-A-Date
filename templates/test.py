isSignedIn = data.cell[isLoggedIn]

hasToken = data.cell[hasToken]


if isSignedIn == "True":

    if hasToken == "True":

        display(myCalendar[data])

    elif hasToken == "False":

        display(notTrueCalendarButFalseWithAdvertisementOptionsLol).withBlur = 2

elif isSignedIn == "False":
    
    display(notTrueCalendarButFalseWithSignUpOptionsLol).withBlur = 2