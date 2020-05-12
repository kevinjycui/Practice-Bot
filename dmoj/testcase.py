class Testcase:

    statusEmojis = {'AC': ':white_check_mark:', 'WA': ':no_entry:', 'TLE': ':snail:', 'RtE': ':warning:', 'IR': ':warning:', 'CE': ':warning:', 'OLE': ':grimacing:', 'MLE': ':elephant:', 'IE': ':face_with_symbols_over_mouth:', 'AB': ':skull:'}
    gradingEmoji = ':hourglass:'

    id = -1
    descriptor = None
    status = None
    details = {}
    
    def __str__(self):
        if self.status in self.statusEmojis.keys():
            statusEmoji = self.statusEmojis[self.status]
        else:
            statusEmoji = self.gradingEmoji
        detailStr = ''
        for entry, data in self.details.items():
            detailStr += entry[0].upper() + entry[1:].lower() + ': ' + data
            if entry != 'points':
                detailStr += ', '
        return '\n**[%d] %s**\n%s %s\n%s\n' % (self.id, self.descriptor, statusEmoji, self.status, detailStr)