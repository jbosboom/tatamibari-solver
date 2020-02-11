parse = (key) ->
  if key?
    match = /^([0-9]*)([\-+| ]?)$/.exec key
    unless match?
      throw new Error "invalid key '#{key}'"
    number = parseInt match[1]
    number = undefined if isNaN number
    number: number
    symbol: match[2]
  else
    number: undefined
    symbol: undefined

horiz = '<rect x="-30" y="-10" width="60" height="20"/>'
vert = '<rect x="-10" y="-30" width="20" height="60"/>'
plus = "#{horiz}\n#{vert}"
mapSymbol =
  '-': horiz
  '|': vert
  '+': plus
  '': ''
  ' ': ''

colors =
  false: 'hsl(360, 50%, 50%)'
  true: 'hsl(214, 50%, 50%)'
  var1x1: 'hsl(36, 50%, 50%)'
  buffer1x1: 'hsl(214, 0%, 50%)'
  special: 'hsl(282, 50%, 50%)'
  yellow: 'hsl(56, 100%, 52%)'

is1x1 = ->
  tile = parse @key
  if tile.symbol == '+' and
     tile.number != parse(@neighbor(-1,0).key).number and
     tile.number != parse(@neighbor(+1,0).key).number and
     tile.number != parse(@neighbor(0,-1).key).number and
     tile.number != parse(@neighbor(0,+1).key).number
    if '+' in [parse(@neighbor(-1,0).key).symbol,
               parse(@neighbor(+1,0).key).symbol,
               parse(@neighbor(0,-1).key).symbol,
               parse(@neighbor(0,+1).key).symbol]
      return colors.buffer1x1
    else
      return colors.var1x1
  null

is2x2 = ->
  tile = parse @key
  for x in [-1,1]
    for y in [-1,1]
      if '+' in [tile.symbol, parse(@neighbor(x,0).key).symbol,
                 parse(@neighbor(x,y).key).symbol,
                 parse(@neighbor(0,y).key).symbol] and
         tile.number == parse(@neighbor(x,0).key).number \
                     == parse(@neighbor(x,y).key).number \
                     == parse(@neighbor(0,y).key).number
        if parse(@neighbor(0,Math.min(0,y)).key).symbol == '+' or
           parse(@neighbor(x,Math.min(0,y)).key).symbol == '+'
          return colors.true
        else
          return colors.false
  null

specials = [
  i: 5
  j: 21 # wide
,
  i: 5
  j: 25 # not wide
,
  i: 9
  j: 15 # not wide
,
  i: 9
  j: 17 # wide
,
  i: 13
  j: 9 # both
,
  i: 19
  j: 4
  color: colors.yellow
  marked: 1
,
  i: 19
  j: 9
  color: colors.yellow
  marked: 1
,
  i: 19
  j: 10
  color: colors.yellow
  marked: 1
,
  i: 19
  j: 15
  color: colors.yellow
  marked: 1
,
  i: 19
  j: 20
  color: colors.yellow #wide
  marked: 1
,
  i: 19
  j: 12
  color: colors.yellow #wide
  marked: 1
,
  i: 19
  j: 25
  color: colors.yellow #wide
  marked: 1
,
  i: 19
  j: 17
  color: colors.yellow #wide
  marked: 1
]

isSpecial = ->
  for special in specials
    if @i == special.i
      row = @row()
      if special.j of row and parse(row[special.j].key).symbol == '-'
        good = true
        for j in [Math.min(@j, special.j)..Math.max(@j, special.j)]
          if parse(row[j].key).number != parse(@key).number
            good = false
            break
        if good
          return special.color ? colors.special
    if special.marked == 1 and @j == special.j
        column = @column()
        if special.i of column and parse(column[special.i].key).symbol == '|'
          good = true
          for i in [Math.min(@i, special.i)..Math.max(@i, special.i)]
            if parse(column[i].key).number != parse(@key).number
              good = false
              break
          if good
            return special.color ? colors.special
  null

(key) -> ->
  tile = parse key
  color = is1x1.call(@) or is2x2.call(@) or isSpecial.call(@) or 'none'
  neighbors = [key, @neighbor(-1,0).key, @neighbor(0,-1).key, @neighbor(-1,-1).key]
  neighbors = (parse(neighbor).number for neighbor in neighbors)
  neighbors.sort()
  if key == ' '
    color = 'black'
  four = (neighbors[3]? and
          neighbors[0] != neighbors[1] != neighbors[2] != neighbors[3])
  """
    <symbol viewBox="-50 -50 100 100" overflowBox="-52.5 -52.5 105 105" style="overflow: visible">
      <rect x="-50" y="-50" width="100" height="100" fill="#{color}"/>
      #{if parse(@neighbor(-1,0).key).number != tile.number and tile.number? then '<line x1="-50" y1="-50" x2="-50" y2="50" stroke="black" stroke-width="5" stroke-linecap="round"/>' else ''}
      #{if parse(@neighbor(0,-1).key).number != tile.number and tile.number? then '<line x1="-50" y1="-50" x2="50" y2="-50" stroke="black" stroke-width="5" stroke-linecap="round"/>' else ''}
      #{if parse(@neighbor(1,0).key).number != tile.number and not parse(@neighbor(1,0).key).number? then '<line x1="50" y1="-50" x2="50" y2="50" stroke="black" stroke-width="5" stroke-linecap="round"/>' else ''}
      #{if parse(@neighbor(0,1).key).number != tile.number and not parse(@neighbor(0,1).key).number? then '<line x1="-50" y1="50" x2="50" y2="50" stroke="black" stroke-width="5" stroke-linecap="round"/>' else ''}
      #{mapSymbol[tile.symbol]}
      #{if four then '<circle cx="-50" cy="-50" r="20" fill="white" stroke="black" stroke-width="15"/>' else ''}
    </symbol>

  """
