import hashlib
import os
import psutil


class PathDirUtil:

    def relative_to_absolute(self, drive, relative_path):
        """
        转换相对路径到绝对路径
        :param drive:  盘符，大写英文字母,如E
        :param relative_path: 相对路径，如xxx/yyy/zzz
        :return: E:/xxx/yyy/zzz
        """
        if not drive.endswith(":"):
            drive += ":"
        if not drive.endswith("/"):
            drive += "/"
        absolute_path = os.path.join(drive, relative_path)
        return absolute_path

    def absolute_to_relative(self, absolute_path):
        """
        转换绝对路径为磁盘分区相对路径
        :param absolute_path: E:/xxx/yyy/zzz
        :return: (E,xxx/yyy/zzz)
        """
        if len(absolute_path) < 3 or absolute_path[1] != ':' or absolute_path[2] != '/':
            raise ValueError("Invalid absolute path format. Expected format is 'Drive:/path/to/directory'.")

            # Extract the drive letter and the relative path
        drive = absolute_path[0]
        relative_path = absolute_path[3:].lstrip("/")

        return drive, relative_path

    def extract_mailbox(self, path):
        """
        从给定的文件路径中提取邮箱后到文件名前的部分。
        参数:
        path (str): 文件路径字符串。
        返回:
        str: 邮箱后到文件名前的路径部分。
        """
        # 使用 os.path.split 分离出每个组件
        parts = path.split(os.sep)

        # 找到最后一个邮箱地址的索引
        email_indices = [i for i, part in enumerate(parts) if '@' in part]

        if not email_indices:
            raise ValueError("邮箱地址未在路径中找到")

        # 使用最后一个邮箱地址的索引
        email_index = email_indices[-1]

        # 邮箱后一部分到最后一个部分（不包括最后一个文件名）
        folder_path = parts[email_index + 1:-1]  # 排除最后一个部分（文件名）

        # 重新组合所需的部分
        return os.sep.join(folder_path)

    def b2GB(self, data):
        return data / (1024 ** 3)

    def b2GB2f(self, data):
        gigabytes = self.b2GB(data)
        # return round(gigabytes, 2)
        return int(gigabytes * 100) / 100

    def b2MB(self, data):
        return data / (1024 ** 2)

    def b2MB2f(self, data):
        gigabytes = self.b2MB(data)
        return int(gigabytes * 100) / 100

    def ensure_directory_structure(self, drive):
        """
        创建MDLStore根文件夹和index子目录
        :param base_path: 盘符
        """
        mdlstore_path = os.path.join(f"{drive}:/", "MDLStore")
        index_path = os.path.join(mdlstore_path, "index")

        if not os.path.exists(mdlstore_path):
            os.makedirs(mdlstore_path)
            print(f"Created directory: {mdlstore_path}")
        else:
            print(f"Directory already exists: {mdlstore_path}")
        # 检查并创建 'index' 子目录
        if not os.path.exists(index_path):
            os.makedirs(index_path)
            print(f"Created directory: {index_path}")
        else:
            print(f"Directory already exists: {index_path}")

    def file_exist_check(self, fullpath):
        """
        检查指定的完整路径的文件是否存在。
        :param fullpath: 文件的完整路径
        :return: 如果文件存在返回 True，否则返回 False
        """
        return os.path.exists(fullpath)

    def file_exist_check(self, drive, base_folder, filename):
        drive = drive + ':/'
        full_path = os.path.join(drive, base_folder, filename)


class StorageManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StorageManager, cls).__new__(cls)
            cls._instance.disk_info = cls._instance.get_disk_info()
            cls._instance.partitions = cls._instance.get_disk_partitions()
        return cls._instance

    def get_disk_partitions(self):
        """获取系统中所有磁盘分区"""
        partitions = psutil.disk_partitions()
        return partitions

    def get_disk_usage(self, path):
        """根据路径获取磁盘使用情况"""
        disk_usage = psutil.disk_usage(path)
        return disk_usage

    def get_available_space(self, path):
        """检查指定路径的可用空间"""
        return psutil.disk_usage(path).free

    def get_disk_info(self):
        """获取所有磁盘的详细信息，包括盘符、容量、已用空间和剩余空间"""
        disk_details = []
        partitions = self.get_disk_partitions()
        for partition in partitions:
            try:
                usage = self.get_disk_usage(partition.mountpoint)
                disk_details.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent_used': usage.percent
                })
            except PermissionError:
                continue
        return disk_details

    def print_disk_info(self):
        """打印所有磁盘的信息"""
        for disk in self.disk_info:
            print(f"Device: {disk['device']} Mounted on: {disk['mountpoint']} "
                  f"Type: {disk['fstype']} Total: {disk['total']} Used: {disk['used']} "
                  f"Free: {disk['free']} Usage: {disk['percent_used']}%")

    def refresh_disk_info(self):
        """刷新磁盘信息，以反映当前系统状态，如新插入的U盘"""
        self.disk_info = self.get_disk_info()
        # print("Disk information has been refreshed.")

    def get_available_disk(self, drive, current_size, change=False):
        """
        获取容量足够保存current_size KB 的磁盘盘符
        :param current_size: 待保存数据量
        :param drive: 初始磁盘，例如“E”
        :param change: 容量不足时，是否切换其他磁盘，比如E盘不足时，询问下个磁盘
        :return: 可用磁盘盘符，若均不可用，则返回None
        """
        current_size_bytes = current_size * 1024  # 将KB转换为字节
        partitions = self.get_disk_partitions()

        for partition in partitions:
            if partition.device.startswith(drive):
                if self.get_available_space(partition.mountpoint) >= current_size_bytes:
                    # return partition.device
                    return partition.device[0]
        if change:
            for partition in partitions:
                if self.get_available_space(partition.mountpoint) >= current_size_bytes:
                    # return partition.device
                    return partition.device[0]

        return None


# class StorageManager:
#     def __init__(self):
#         self.disk_info = self.get_disk_info()
#
#     def get_disk_partitions(self):
#         """ 获取系统中所有磁盘分区 """
#         partitions = psutil.disk_partitions()
#         return partitions
#
#     def get_disk_usage(self, path):
#         """ 根据路径获取磁盘使用情况 """
#         disk_usage = psutil.disk_usage(path)
#         return disk_usage
#
#     def get_disk_info(self):
#         """ 获取所有磁盘的详细信息，包括盘符、容量、已用空间和剩余空间 """
#         disk_details = []
#         partitions = self.get_disk_partitions()
#         for partition in partitions:
#             try:
#                 usage = self.get_disk_usage(partition.mountpoint)
#                 disk_details.append({
#                     'device': partition.device,
#                     'mountpoint': partition.mountpoint,
#                     'fstype': partition.fstype,
#                     'total': usage.total,
#                     'used': usage.used,
#                     'free': usage.free,
#                     'percent_used': usage.percent
#                 })
#             except PermissionError:
#                 # 某些分区可能没有权限访问
#                 continue
#         return disk_details
#
#     def print_disk_info(self):
#         """ 打印所有磁盘的信息 """
#         for disk in self.disk_info:
#             print(f"Device: {disk['device']} Mounted on: {disk['mountpoint']} "
#                   f"Type: {disk['fstype']} Total: {disk['total']} Used: {disk['used']} "
#                   f"Free: {disk['free']} Usage: {disk['percent_used']}%")


class FileWriter:

    def __init__(self):
        self.storage_manager = StorageManager()  # 使用已经存在的StorageManager单例

    def get_available_space(self, path):
        """使用psutil检查指定路径的可用空间"""
        return psutil.disk_usage(path).free

    # def write_file(self, file_data, filename, drive, base_folder, change=False):
    #     """
    #     将文件数据写入指定磁盘的指定文件夹中。如果指定磁盘空间不足，可选择性地切换到另一个磁盘。
    #     :param file_data: 要写入文件的数据
    #     :param filename: 要创建的文件名
    #     :param drive: 初始驱动器字母（例如：'E'）
    #     :param base_folder: 相对于驱动器根目录的文件夹路径
    #     :param change: 如果首选驱动器空间不足，是否尝试使用另一个驱动器
    #     :return: 文件最终存储的绝对路径，如果操作失败则返回 None
    #     """
    #     # Try writing to the specified drive first
    #     drive = drive + ':/'
    #     full_path = os.path.join(drive, base_folder, filename)
    #     if not self._write_to_disk(full_path, file_data, drive):
    #         if change:
    #             # Get all available partitions
    #             partitions = self.storage_manager.partitions
    #             for partition in partitions:
    #                 print(partition)
    #                 if partition.device != drive:  # Skip the initial drive
    #                     full_path = os.path.join(partition.mountpoint, base_folder, filename)
    #                     if self._write_to_disk(full_path, file_data, partition.device):
    #                         return full_path
    #         return None  # 存储不足返回None
    #     return full_path  # Return the path where the file was successfully written

    def write_file(self, file_data, filename, drive, base_folder, change=False):
        """
        将文件数据写入指定磁盘的指定文件夹中。如果指定磁盘空间不足，可选择性地切换到另一个磁盘。
        :param file_data: 要写入文件的数据
        :param filename: 要创建的文件名
        :param drive: 初始驱动器字母（例如：'E'）
        :param base_folder: 相对于驱动器根目录的文件夹路径
        :param change: 如果首选驱动器空间不足，是否尝试使用另一个驱动器
        :return: 文件最终存储的绝对路径，如果操作失败则返回 None
        """
        # 尝试首先写入指定驱动器
        drive = drive + ':/'
        full_path = os.path.join(drive, base_folder, filename)
        full_path = self._handle_existing_file(full_path, file_data)
        if not self._write_to_disk(full_path, file_data, drive):
            if change:
                partitions = self.storage_manager.partitions
                for partition in partitions:
                    print(partition)
                    if partition.device != drive:  # Skip the initial drive
                        full_path = os.path.join(partition.mountpoint, base_folder, filename)
                        if self._write_to_disk(full_path, file_data, partition.device):
                            return full_path
            return None  # 存储不足返回None
        return full_path  # Return the path where the file was successfully written

    def get_file_hash(self, file_path):
        hash_algo = hashlib.md5()
        with open(file_path, 'rb') as file:
            while chunk := file.read(8192):
                hash_algo.update(chunk)
        return hash_algo.hexdigest()

    def get_file_size(self, file_path):
        """获取文件的大小（以字节为单位）"""
        return os.path.getsize(file_path)

    def _handle_existing_file(self, full_path, file_data):
        if os.path.exists(full_path):
            existing_hash = self.get_file_hash(full_path)
            new_hash = hashlib.md5(file_data).hexdigest()
            if existing_hash == new_hash:
                return full_path
            else:
                # print(f'旧文件大小{self.get_file_size(full_path)}新文件大小{len(file_data)}')
                # print(f'文件{full_path}和新的文件内容哈希不一致')
                return self._ensure_unique_filename(full_path, file_data)
        return full_path

    # def _handle_existing_file(self, full_path, file_data):
    #     """
    #     处理目标路径上已经存在的文件。如果文件存在且内容相同，则覆盖，否则生成新的唯一文件名。
    #     :param full_path: 目标文件的完整路径
    #     :param file_data: 要写入的文件数据
    #     :return: 处理后的唯一文件路径
    #     """
    #     if os.path.exists(full_path):
    #         with open(full_path, 'rb') as existing_file:
    #             existing_data = existing_file.read()
    #             if existing_data == file_data:
    #                 return full_path
    #             else:
    #                 print(f'文件{full_path}和新的{full_path}内容不一致')
    #                 return self._ensure_unique_filename(full_path)
    #     return full_path

    def _ensure_unique_filename(self, path, file_data):
        """
        确保文件名唯一。如果文件已存在，则在文件名后添加序号。
        :param path: 原始文件路径
        :param file_data: 文件数据
        :return: 唯一文件路径
        """
        base, extension = os.path.splitext(path)
        counter = 1
        unique_path = path
        file_hash = hashlib.md5(file_data).hexdigest()

        while os.path.exists(unique_path):
            existing_hash = self.get_file_hash(unique_path)
            if existing_hash == file_hash:
                print(f'存在一个一致的文件{unique_path}')
                return unique_path

            unique_path = f"{base}_{counter}{extension}"
            counter += 1

        return unique_path

    # def _ensure_unique_filename(self, path, file_data):
    #     """
    #     确保文件名唯一。如果文件已存在，则在文件名后添加序号。
    #     :param path: 原始文件路径
    #     :return: 唯一文件路径
    #     """
    #     base, extension = os.path.splitext(path)
    #     counter = 1
    #     unique_path = path
    #     while os.path.exists(unique_path):
    #         unique_path = f"{base}_{counter}{extension}"
    #
    #         existing_hash = self.get_file_hash(unique_path)
    #         new_hash = hashlib.md5(file_data).hexdigest()
    #         if existing_hash == new_hash:
    #             return unique_path
    #
    #         counter += 1
    #     return unique_path

    def _write_to_disk(self, full_path, file_data, drive):
        """尝试向目标位置写文件"""
        # if self.get_available_space(drive) > 1000*(2**30):
        if self.get_available_space(drive) > len(file_data):
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'wb') as f:
                f.write(file_data)
            return True
        return False

    def copy_file(self, abstract_path, new_name, drive, base_folder, change=False):
        """
        将文件数据写入指定磁盘的指定文件夹中。如果指定磁盘空间不足，可选择性地切换到另一个磁盘。
        :param new_name:
        :param abstract_path: 绝对路径，如E:/MDLStore/data.txt
        :param drive: 初始目标驱动器字母（例如：'E'）
        :param base_folder: 相对于驱动器根目录的文件夹路径，如MDLStore/data.txt
        :param change: 如果首选驱动器空间不足，是否尝试使用另一个驱动器
        :return: 文件最终存储的绝对路径，如果操作失败则返回 None
        """
        try:
            # 读取源文件数据
            with open(abstract_path, 'rb') as file:
                file_data = file.read()
        except Exception as e:
            print(f"Failed to read source file: {e}")
            return None

            # 提取文件名从路径
        # filename = os.path.basename(abstract_path)
        filename = new_name

        # 使用write_file方法写文件到新位置
        result_path = self.write_file(file_data, filename, drive, base_folder, change)
        # 返回新文件路径或None（如果写入失败）
        return result_path


def test():
    # 首先创建 StorageManager 的实例
    storage_manager = StorageManager()
    # 刷新
    storage_manager.refresh_disk_info()
    partitions = storage_manager.get_disk_partitions()

    result_partition = []
    for partition in partitions:
        print(f"Device: {partition.device}, Mountpoint: {partition.mountpoint}, Fstype: {partition.fstype}")
        result_partition.append(partition.device[0])

    # 再次打印所有磁盘的信息以查看更新后的状态
    storage_manager.print_disk_info()
