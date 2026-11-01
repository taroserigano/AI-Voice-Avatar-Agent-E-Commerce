Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SelectVoice('Microsoft Zira Desktop')
$synth.SetOutputToWaveFile((Join-Path $PSScriptRoot 'narration.wav'))
$ssml = @'
<speak version="1.0" xml:lang="en-US" xmlns="http://www.w3.org/2001/10/synthesis">
  <prosody rate="-8%">Meet Xana.</prosody>
  <break time="550ms"/>
  <prosody rate="-8%">Ask about your order by voice or text.</prosody>
  <break time="550ms"/>
  <prosody rate="-8%">See a clear return quote.</prosody>
  <break time="450ms"/>
  <prosody rate="-8%">Nothing starts until you confirm.</prosody>
</speak>
'@
try { $synth.SpeakSsml($ssml) } finally { $synth.Dispose() }
