/*
 Copyright (C) 2021 Matt Clarke
 
 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.
 
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License along
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
*/

// Logger tweak to dump data io

#import <os/log.h>

static os_log_t logger;

%hook HMDAVControl

- (BOOL)onUdpSocket:(id)sock didReceiveData:(NSData *)data withTag:(long)tag fromHost:(NSString *)host port:(UInt16)port {
    BOOL result = %orig;
    
    os_log(logger, "HMDAVControl onUdpSocket:didReceiveData:withTag:fromHost:port: -- data %@, tag %ld, host %@, port %d", data, tag, host, port);
    
    return result;
}

- (void)onSocket:(id)sock didReadData:(NSData *)data withTag:(long)tag {
    os_log(logger, "HMDAVControl onSocket:didReadData:withTag: -- data %@, tag %ld", data, tag);
    
    %orig;
}

- (void)handleUDPString:(NSString*)string {
    %orig;
    
    os_log(logger, "HMDAVControl handleUDPString: -- %@", string);
}

- (void)heartbeatAction {
    os_log(logger, "HMDAVControl -- heartbeatAction");
    %orig;
}

-(void)initSocket {
    os_log(logger, "HMDAVControl -- initSocket");
    %orig;
}

%end

%hook AsyncUdpSocket

- (BOOL)bindToPort:(UInt16)port error:(NSError **)errPtr {
    BOOL result = %orig;
    
    os_log(logger, "AsyncUdpSocket bindToPort:error: -- port %d", port);
    
    return result;
}

- (BOOL)bindToAddress:(NSString *)localAddr port:(UInt16)port error:(NSError **)errPtr {
    BOOL result = %orig;
    
    os_log(logger, "AsyncUdpSocket bindToAddress:port:error: -- address %@, port %d", localAddr, port);
    
    return result;
}

- (BOOL)sendData:(NSData *)data toHost:(NSString *)host port:(UInt16)port withTimeout:(NSTimeInterval)timeout tag:(long)tag {
    
    BOOL result = %orig;
    
    os_log(logger, "AsyncUdpSocket sendData:toHost:port:withTimeout:tag: -- data %@, host %@, port %d, timeout %f, tag: %ld", data, host, port, timeout, tag);
    
    return result;
}

%end

%hook AsyncSocket

- (BOOL)connectToHost:(NSString*)hostname onPort:(UInt16)port error:(NSError **)errPtr {
    BOOL result = %orig;
    
    os_log(logger, "AsyncSocket connectToHost:onPort:error: -- host %@, port %d", hostname, port);
    
    return result;
}

- (void)writeData:(NSData *)data withTimeout:(NSTimeInterval)timeout tag:(long)tag {
    os_log(logger, "AsyncSocket writeData:withTimeout:tag: -- data %@, timeout %f, tag: %ld", data, timeout, tag);
    %orig;
}

%end

%ctor {
    logger = os_log_create("com.matchstic.minirclogger", "log");
    
    %init;
    
    os_log(logger, "MATCHSTIC IS IN DA HOUSE");
}
