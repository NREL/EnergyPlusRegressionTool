"""html data to be used by other modules"""

# Copyright (C) 2009 Santosh Philip
# This file is part of tablediff.
# 
# tablediff is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# tablediff is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with tablediff.  If not, see <http://www.gnu.org/licenses/>.
# VERSION: 1.0


titlecss = """<!DOCTYPE html PUBLIC "-
//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"><html xmlns="http://www.w3.org/1999/xhtml">
<head><title>%s</title>  <style type="text/css"> %s </style>
<meta name="generator" content="BBEdit 8.2" /></head>
<body></body></html>
"""

titlehtml = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
	<title>%s</title>
	<meta name="generator" content="BBEdit 8.2" />
</head>
<body>

</body>
</html>
"""


thecss = """td.big {
	background-color: #FF969D;
}

td.small {
	background-color: #FFBE84;
}

td.equal {
	background-color: #CBFFFF;
}
	
td.table_size_error {
	background-color: #FCFF97;
} 
.big {
	background-color: #FF969D;
}

.small {
	background-color: #FFBE84;
}

"""
