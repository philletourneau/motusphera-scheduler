from animations import AnimationScheduler, SineWaveAnimation, LinearAnimation, AnimationGroupAdditive

def setup_scheduler():
    scheduler = AnimationScheduler()
    
    # Define animations with start times in seconds
    myLinearAnimation = LinearAnimation(starttime=30, speed=0.7, min_value=0.01, max_value=0.6)
    mySineWaveAnimation = SineWaveAnimation(starttime=0, speed=0.32, min_value=0.0, max_value=0.9, frequency_multiplier=2.0, wavelength_modifier=0.5)

    myGroupAnimation = AnimationGroupAdditive(starttime=50, animations=[mySineWaveAnimation, myLinearAnimation])
    # Append animations to scheduler
    ## BUG the order they're appended makes a difference, it shouldnt'
    scheduler.appendToQueue(mySineWaveAnimation)
    scheduler.appendToQueue(myLinearAnimation)
    scheduler.appendToQueue(myGroupAnimation)
    
    return scheduler
