#!/usr/bin/env python

HEADERS = ( 'Account', 'Action', 'ActionID', 'AOCBillingId', 'Application', 'Async', 'AuthType', 'CallerID', 
'Category', 'Cause', 'Channel', 'ChannelPrefix', 'ChargeType', 'ChargingAssociationId', 'ChargingAssociationNumber', 
'ChargingAssociationPlan', 'Codecs', 'Command', 'Context', 'CurrencyAmount', 'CurrencyMultiplier', 'CurrencyName', 
'Data', 'DstFilename', 'EventMask', 'Events', 'Exten', 'ExtraChannel', 'ExtraContext', 'ExtraExten', 'ExtraPriority', 
'Filename', 'Key', 'LoadType', 'Mailbox', 'MD5', 'Message', 'Module', 'MsgType', 'Priority', 'Reload', 'Secret', 
'SrcFilename', 'SuppressEvents', 'Timeout', 'TotalType', 'UserEvent', 'Username', 'Value', 'Variable', 'Variables', )

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

