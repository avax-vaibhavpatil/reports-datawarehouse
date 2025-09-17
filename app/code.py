# You are given an array of integers. Your task is to find the maximum difference between two elements
#  such that the larger element comes after the smaller element.

arr = [2, 3, 10, 6, 4, 8, 1]

def max_diff(arr):
    n = len(arr)
    max_diff = arr[0]

    for i in range(n):
        for j in range(i+1, n):
            if arr[j] - arr[i] > max_diff:
                max_diff = arr[j] - arr[i]
    return max_diff

print(max_diff(arr))


def max_diff(arr):
    n = len(arr)
    min_ele = arr[0]
    max_diff = arr[1] - arr[0]

    for i in range(1, n):
        diff = arr[i] - min_ele

        if diff > max_diff :
            max_diff = diff

        if arr[i] < min_ele:
            min_ele = arr[i]

    return max_diff

print(max_diff(arr))
        

Input:  arr = [0, 1, 9, 8, 4, 0, 0, 2, 7, 0, 6, 0]
Output: [1, 9, 8, 4, 2, 7, 6, 0, 0, 0, 0, 0]

def move_zeros(arr):
    n = len(arr)
    count = 0

    for i in range(n):
        if arr[i] != 0:
            arr[count] = arr[i]
            count += 1

    while count < n:
        arr[count] = 0
        count += 1

    return arr
        
