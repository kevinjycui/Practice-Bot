class Result:

    statusEmojis = {'AC': ':white_check_mark:', 'WA': ':no_entry:', 'TLE': ':snail:', 'RtE': ':warning:', 'IR': ':warning:', 'CE': ':warning:', 'OLE': ':grimacing:', 'MLE': ':elephant:', 'IE': ':face_with_symbols_over_mouth:', 'AB': ':skull:'}
    gradingEmoji = ':hourglass:'
    
    def __init__(self, cases, raw_result, status, problemName, time, memory, done=False):
        self.cases = cases
        self.raw_result = raw_result
        self.status = status
        self.problemName = problemName
        self.time = time
        if time is None:
            self.time = 'Time N/A'
        self.memory = memory
        if memory is None:
            self.memory = 'Memory N/A'
        self.done = done

    def __str__(self):
        if self.status in self.statusEmojis.keys():
            statusEmoji = self.statusEmojis[self.status]
        else:
            statusEmoji = self.gradingEmoji
        return '**' + self.problemName + '**\n' + statusEmoji + ' ' + self.status +'\n' + self.time + ', ' + self.memory + '\n' + ('Complete!' if self.done else 'Pending...') + '\n' + '\n'.join(map(str, self.cases))
