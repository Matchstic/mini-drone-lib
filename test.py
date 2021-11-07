def computeControlFormat():
    mSpeedValue = 0x1 # 0x0, 0x1, 0x2 for slow/mid/fast
    
    leftTrim = 0x10 # min 00, max 1f
    rightTrim = 0x10 # min 00, max 1f
    rRightTrim = 0x10 # min 00, max 1f
    
    onekeyFly = False
    onekeyDrop = False
    returnFlag = False
    reverseFly = False # (fanzhuanFly)
    headlessMode = False # (wutou)
    stopFlight = False # kills motors
    calibrateGyro = False # (xiaozhun)
    finalised = True
    
    
    # Rough translation from disassembly
    
    yaw = 0x64 # leftCirclePowerLR, 0x00 to 0xff
    throttle = 0x64 # leftCirclePowerFB, 0x00 to 0xff
    
    roll = 0x64 # rightCirclePowerLR, 0x00 to 0xff
    pitch = 0x64 # rightCirclePowerFB, 0x00 to 0xff
    
    trimBytes = None

    # throttle handling
    if finalised:
        if not onekeyFly:
            if not onekeyDrop:
                trimBytes = leftTrim | 0xffffffffffffff80
            else:
                trimBytes = leftTrim & 0x7f
        else:
            trimBytes = leftTrim | 0xffffffffffffff80
    else:
        trimBytes = leftTrim & 0x7f
        
        
    # Handle gyro calibration flag
    # r24 is now containing the result
    # trimBytes = trimBytes | (0x1 if calibrateGyro else 0x0) * 0x40
    
    # Handle flags
    
    #flags = mSpeedValue
    #flags = flags | (0x1 if reverseFly else 0x0) * 0x4
    #flags = flags | (0x1 if returnFlag else 0x0) * 0x8 | (0x1 if stopFlight else 0x0) * 0x20
    #flags = flags | (0x1 if onekeyFly else 0x0) * 0x40
    #flags = flags | (0x1 if onekeyDrop else 0x0) * 0x80
    #flags = flags | (0x1 if headlessMode else 0x0) * 0x10
    flags = 0x1
    
    # throttle/yaw/pitch/roll
    
    # wtf?
    if yaw <= 0x2:
        yaw = 0x0
    
    if throttle >= 0x7e:
        throttle = 0x7f
    elif throttle <= 0x0:
        throttle = 0x0
        
    if pitch >= 0x7e:
        pitch = 0x7e
    elif pitch <= 0x0:
        pitch = 0x0
        
    if roll >= 0x7e:
        roll = 0x7e
    elif roll <= 0x0:
        roll = 0x0
    
    return 0x8ff - flags - yaw - throttle - roll - pitch - trimBytes - rRightTrim - rightTrim;

if __name__ == '__main__':
    print(computeControlFormat())