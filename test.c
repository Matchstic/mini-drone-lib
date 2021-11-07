#include <stdio.h>

int main(int argc, char **argv) {    
    unsigned char yaw = 0x64; // 0x00 to 0xff
    unsigned char throttle = 0x64; 
    unsigned char roll = 0x64;
    unsigned char pitch = 0x64;
    
    unsigned char leftTrim = 0x10; // min 00, max 1f
    unsigned char rightTrim = 0x10; // min 00, max 1f
    unsigned char rRightTrim = 0x10; // min 00, max 1f
    
    unsigned char bytes[11] = [0xff, 0x08, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0];
    
    
    
    long trimBytes = leftTrim | 0xffffffffffffff80;
    
    unsigned char flags = 0x1;
    
    // unsigned char bytes[11] = 0x8ff - flags - yaw - throttle - roll - pitch - trimBytes - rRightTrim - rightTrim;
    
    printf("%lx\n", 0x8ff - flags - var_62 - yaw - throttle - roll - pitch - trimBytes - rRightTrim - rightTrim);
    
    return 0;
}