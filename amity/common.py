#!/usr/bin/env python
#
#Copyright (c) 2012  Shane R. Spencer
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#of the Software, and to permit persons to whom the Software is furnished to do
#so, subject to the following conditions: 
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software. 
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

KEYS = ( 'Account', 'Action', 'ActionID', 'AOCBillingId', 'Application', 'Async', 'AuthType', 'CallerID', 'Category', 
'Cause', 'Channel', 'ChannelPrefix', 'ChargeType', 'ChargingAssociationId', 'ChargingAssociationNumber', 
'ChargingAssociationPlan', 'Codecs', 'Command', 'Context', 'CurrencyAmount', 'CurrencyMultiplier', 'CurrencyName', 
'Data', 'DstFilename', 'EventMask', 'Events', 'Exten', 'ExtraChannel', 'ExtraContext', 'ExtraExten', 'ExtraPriority', 
'Filename', 'Key', 'LoadType', 'Mailbox', 'MD5', 'Message', 'Module', 'MsgType', 'Priority', 'Reload', 'Secret', 
'SrcFilename', 'SuppressEvents', 'Timeout', 'TotalType', 'UserEvent', 'Username', 'Value', 'Variable', 'Variables', 
'UUID' ,'Method')

KEYALIAS = {}
for key in KEYS: KEYALIAS[key.lower()] = key

VALUES = ()

VALUEALIAS = {}
for value in VALUES: VALUEALIAS[value.lower()] = value

VALUENEVERALIAS = ('Username', 'Secret',)

COMMANDS = ( 'AbsoluteTimeout', 'AgentLogoff', 'Agents', 'AGI', 'AOCMessage', 'Atxfer', 'Bridge', 'Challenge', 
'ChangeMonitor', 'Command', 'CoreSettings', 'CoreShowChannels', 'CoreStatus', 'CreateConfig', 'DAHDIDialOffhook', 
'DAHDIDNDoff', 'DAHDIDNDon', 'DAHDIHangup', 'DAHDIRestart', 'DAHDIShowChannels', 'DAHDITransfer', 'DataGet', 'DBDel', 
'DBDelTree', 'DBGet', 'DBPut', 'Events', 'ExtensionState', 'GetConfig', 'GetConfigJSON', 'Getvar', 'Hangup', 
'IAXnetstats', 'IAXpeerlist', 'IAXpeers', 'IAXregistry', 'JabberSend', 'ListCategories', 'ListCommands', 
'LocalOptimizeAway', 'Login', 'Logoff', 'MailboxCount', 'MailboxStatus', 'MeetmeList', 'MeetmeMute', 'MeetmeUnmute', 
'MixMonitorMute', 'ModuleCheck', 'ModuleLoad', 'Monitor', 'Originate', 'Park', 'ParkedCalls', 'PauseMonitor', 'Ping', 
'PlayDTMF', 'QueueAdd', 'QueueLog', 'QueuePause', 'QueuePenalty', 'QueueReload', 'QueueRemove', 'QueueReset', 
'QueueRule', 'Queues', 'QueueStatus', 'QueueSummary', 'Redirect', 'Reload', 'SendText', 'Setvar', 'ShowDialPlan', 
'SIPnotify', 'SIPpeers', 'SIPqualifypeer', 'SIPshowpeer', 'SIPshowregistry', 'SKINNYdevices', 'SKINNYlines', 
'SKINNYshowdevice', 'SKINNYshowline', 'Status', 'StopMonitor', 'UnpauseMonitor', 'UpdateConfig', 'UserEvent', 
'VoicemailUsersList', 'WaitEvent', )

COMMANDALIAS = {}
for command in COMMANDS: COMMANDALIAS[command.lower()] = command

