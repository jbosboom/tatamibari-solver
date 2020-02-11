parse = (key) ->
  if key?
    match = /^([\-+| .]?)([abcm]?)$/.exec key
    unless match?
      throw new Error "invalid key '#{key}'"
    symbol: match[1]
    type: match[2]
  else
    symbol: undefined
    type: undefined

horiz = <rect x="-30" y="-10" width="60" height="20"/>
vert = <rect x="-10" y="-30" width="20" height="60"/>
plus = <>{horiz}{vert}</>
mapSymbol =
  '-': horiz
  '|': vert
  '+': plus
  '': ''
  ' ': ''
  '.': ''

colors = require './unsolved-colors.coffee'
colors[''] = 'none'

(key) -> ->
  tile = parse key
  color = colors[tile.type]
  <symbol viewBox="-50 -50 100 100" overflowBox="-52.5 -52.5 105 105" style="overflow: visible">
    <rect x="-50" y="-50" width="100" height="100" fill={color}/>
    <line x1="-50" y1="-50" x2="-50" y2="50" stroke="#808080" stroke-width="5" stroke-linecap="round"/>
    <line x1="-50" y1="-50" x2="50" y2="-50" stroke="#808080" stroke-width="5" stroke-linecap="round"/>
    <line x1="50" y1="-50" x2="50" y2="50" stroke="#808080" stroke-width="5" stroke-linecap="round"/>
    <line x1="-50" y1="50" x2="50" y2="50" stroke="#808080" stroke-width="5" stroke-linecap="round"/>
    {mapSymbol[tile.symbol]}
  </symbol>
